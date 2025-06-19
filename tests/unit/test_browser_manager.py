"""Unit tests for BrowserManager component."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from playwright.async_api import Browser, BrowserContext, Page, Playwright

from flight_scraper.core.browser_manager import BrowserManager
from flight_scraper.core.models import ScrapingError


class TestBrowserManager:
    """Test BrowserManager component."""

    def test_init(self):
        """Test BrowserManager initialization."""
        manager = BrowserManager(headless=True)
        assert manager.headless is True
        assert manager.browser is None
        assert manager.context is None
        assert manager.page is None
        assert manager.playwright is None

    def test_init_default_headless(self):
        """Test BrowserManager default headless setting."""
        manager = BrowserManager()
        assert manager.headless is False

    @pytest.mark.asyncio
    async def test_context_manager_success(self):
        """Test successful async context manager usage."""
        with (
            patch.object(BrowserManager, "initialize") as mock_init,
            patch.object(BrowserManager, "cleanup") as mock_cleanup,
        ):

            mock_init.return_value = None
            mock_cleanup.return_value = None

            async with BrowserManager(headless=True) as manager:
                assert isinstance(manager, BrowserManager)

            mock_init.assert_called_once()
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_init_failure(self):
        """Test async context manager with initialization failure."""
        manager = BrowserManager(headless=True)

        with (
            patch.object(manager, "initialize") as mock_init,
            patch.object(manager, "cleanup") as mock_cleanup,
        ):

            mock_init.side_effect = ScrapingError("Init failed")
            mock_cleanup.return_value = None

            with pytest.raises(ScrapingError, match="Init failed"):
                async with manager:
                    pass

            mock_init.assert_called_once()
            # __aexit__ is NOT called when __aenter__ raises an exception
            # This is the correct Python async context manager behavior
            mock_cleanup.assert_not_called()

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful browser initialization."""
        manager = BrowserManager(headless=True)

        # Mock Playwright components
        mock_playwright = AsyncMock(spec=Playwright)
        mock_browser = AsyncMock(spec=Browser)
        mock_context = AsyncMock(spec=BrowserContext)
        mock_page = AsyncMock(spec=Page)

        mock_chromium = AsyncMock()
        mock_chromium.launch.return_value = mock_browser
        mock_playwright.chromium = mock_chromium

        mock_browser.new_context.return_value = mock_context
        mock_context.add_init_script.return_value = None
        mock_context.new_page.return_value = mock_page

        with patch("flight_scraper.core.browser_manager.async_playwright") as mock_async_playwright:
            # Create a proper mock for async_playwright() that returns an object with start()
            mock_playwright_instance = Mock()
            mock_playwright_instance.start = AsyncMock(return_value=mock_playwright)
            mock_async_playwright.return_value = mock_playwright_instance

            await manager.initialize()

            assert manager.playwright == mock_playwright
            assert manager.browser == mock_browser
            assert manager.context == mock_context
            assert manager.page == mock_page

            # Verify browser launch with correct arguments
            mock_chromium.launch.assert_called_once_with(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                ],
            )

            # Verify context creation with user agent and viewport
            mock_browser.new_context.assert_called_once()
            call_args = mock_browser.new_context.call_args
            assert "user_agent" in call_args.kwargs
            assert "viewport" in call_args.kwargs

            # Verify stealth script injection
            mock_context.add_init_script.assert_called_once()

            # Verify page configuration
            mock_page.set_default_timeout.assert_called_once()
            mock_page.set_default_navigation_timeout.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_playwright_failure(self):
        """Test initialization failure during Playwright startup."""
        manager = BrowserManager(headless=True)

        with patch("flight_scraper.core.browser_manager.async_playwright") as mock_async_playwright:
            mock_async_playwright.return_value.start.side_effect = Exception("Playwright failed")

            with patch.object(manager, "cleanup") as mock_cleanup:
                with pytest.raises(ScrapingError, match="Browser initialization failed"):
                    await manager.initialize()

                mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_browser_launch_failure(self):
        """Test initialization failure during browser launch."""
        manager = BrowserManager(headless=True)

        mock_playwright = AsyncMock(spec=Playwright)
        mock_chromium = AsyncMock()
        mock_chromium.launch.side_effect = Exception("Browser launch failed")
        mock_playwright.chromium = mock_chromium

        with patch("flight_scraper.core.browser_manager.async_playwright") as mock_async_playwright:
            # Create a mock that returns an awaitable object with a start method
            mock_async_playwright.return_value.start = AsyncMock(return_value=mock_playwright)

            with patch.object(manager, "cleanup") as mock_cleanup:
                with pytest.raises(ScrapingError, match="Browser initialization failed"):
                    await manager.initialize()

                mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_success(self):
        """Test successful cleanup of all resources."""
        manager = BrowserManager(headless=True)

        # Set up mock resources
        mock_context = AsyncMock(spec=BrowserContext)
        mock_browser = AsyncMock(spec=Browser)
        mock_playwright = AsyncMock(spec=Playwright)

        manager.context = mock_context
        manager.browser = mock_browser
        manager.playwright = mock_playwright

        await manager.cleanup()

        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_partial_resources(self):
        """Test cleanup with only some resources initialized."""
        manager = BrowserManager(headless=True)

        # Only set browser, not context or playwright
        mock_browser = AsyncMock(spec=Browser)
        manager.browser = mock_browser

        await manager.cleanup()

        # Only browser should be closed
        mock_browser.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_with_errors(self):
        """Test cleanup handles individual resource cleanup errors."""
        manager = BrowserManager(headless=True)

        mock_context = AsyncMock(spec=BrowserContext)
        mock_browser = AsyncMock(spec=Browser)
        mock_playwright = AsyncMock(spec=Playwright)

        # Make context close fail
        mock_context.close.side_effect = Exception("Context close failed")

        manager.context = mock_context
        manager.browser = mock_browser
        manager.playwright = mock_playwright

        # Should not raise exception, just log error
        await manager.cleanup()

        # Verify all cleanup methods were attempted despite the context error
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()

    def test_get_page_success(self):
        """Test successful page retrieval."""
        manager = BrowserManager(headless=True)
        mock_page = Mock(spec=Page)
        manager.page = mock_page

        result = manager.get_page()
        assert result == mock_page

    def test_get_page_not_initialized(self):
        """Test page retrieval when not initialized."""
        manager = BrowserManager(headless=True)

        with pytest.raises(ScrapingError, match="Browser not initialized"):
            manager.get_page()

    def test_is_initialized_true(self):
        """Test is_initialized when all components are present."""
        manager = BrowserManager(headless=True)
        manager.browser = Mock(spec=Browser)
        manager.context = Mock(spec=BrowserContext)
        manager.page = Mock(spec=Page)

        assert manager.is_initialized() is True

    def test_is_initialized_false(self):
        """Test is_initialized when components are missing."""
        manager = BrowserManager(headless=True)

        # No components initialized
        assert manager.is_initialized() is False

        # Only browser initialized
        manager.browser = Mock(spec=Browser)
        assert manager.is_initialized() is False

        # Browser and context initialized
        manager.context = Mock(spec=BrowserContext)
        assert manager.is_initialized() is False

        # All components initialized
        manager.page = Mock(spec=Page)
        assert manager.is_initialized() is True
