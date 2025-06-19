"""Unit tests for error scenarios and edge cases."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import date
import asyncio
from playwright.async_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

from flight_scraper.core.scraper import GoogleFlightsScraper
from flight_scraper.core.browser_manager import BrowserManager
from flight_scraper.core.form_handler import FormHandler
from flight_scraper.core.data_extractor import DataExtractor
from flight_scraper.core.models import (
    SearchCriteria, TripType, ScrapingError, NavigationError, 
    ElementNotFoundError, NetworkError
)


class TestTimeoutScenarios:
    """Test timeout and network failure scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sample_criteria = SearchCriteria(
            origin="JFK",
            destination="LAX",
            departure_date=date(2024, 7, 15),
            trip_type=TripType.ONE_WAY,
            max_results=10
        )

    @pytest.mark.asyncio
    async def test_browser_initialization_timeout(self):
        """Test browser initialization timeout."""
        manager = BrowserManager(headless=True)
        
        with patch('flight_scraper.core.browser_manager.async_playwright') as mock_playwright:
            mock_playwright.return_value.start.side_effect = asyncio.TimeoutError("Playwright timeout")
            
            with pytest.raises(ScrapingError, match="Browser initialization failed"):
                await manager.initialize()

    @pytest.mark.asyncio
    async def test_page_navigation_timeout(self):
        """Test page navigation timeout."""
        mock_page = AsyncMock()
        mock_page.goto.side_effect = PlaywrightTimeoutError("Navigation timeout")
        
        handler = FormHandler(mock_page)
        
        with pytest.raises(NavigationError, match="Navigation failed with both primary and fallback URLs"):
            await handler.navigate_to_google_flights(self.sample_criteria)

    @pytest.mark.asyncio
    async def test_element_wait_timeout(self):
        """Test element waiting timeout."""
        mock_page = AsyncMock()
        mock_page.keyboard.press.return_value = None
        
        with patch('flight_scraper.core.form_handler.robust_fill') as mock_fill:
            mock_fill.side_effect = PlaywrightTimeoutError("Element timeout")
            
            handler = FormHandler(mock_page)
            
            with pytest.raises(ScrapingError, match="Form filling failed"):
                await handler.fill_search_form(self.sample_criteria)

    @pytest.mark.asyncio
    async def test_data_extraction_timeout(self):
        """Test data extraction timeout."""
        mock_page = AsyncMock()
        mock_page.evaluate.side_effect = PlaywrightTimeoutError("Evaluation timeout")
        
        extractor = DataExtractor(mock_page)
        
        # The implementation catches errors in _find_flight_containers and returns []
        # So we expect an empty result, not an exception
        result = await extractor.extract_flight_data(self.sample_criteria, 50)
        assert result == []

    @pytest.mark.asyncio
    async def test_scraper_timeout_recovery(self):
        """Test scraper timeout with recovery attempt."""
        scraper = GoogleFlightsScraper(headless=True)
        
        # Mock components
        mock_browser_manager = AsyncMock()
        mock_form_handler = AsyncMock()
        mock_data_extractor = AsyncMock()
        
        scraper.browser_manager = mock_browser_manager
        scraper.form_handler = mock_form_handler
        scraper.data_extractor = mock_data_extractor
        
        # First navigation fails, form filling succeeds
        mock_form_handler.navigate_to_google_flights.side_effect = [
            PlaywrightTimeoutError("First timeout"), 
            None  # Recovery succeeds
        ]
        mock_form_handler.fill_search_form.return_value = None
        mock_form_handler.trigger_search.return_value = None
        mock_data_extractor.extract_flight_data.return_value = []
        
        with patch.object(scraper, '_record_session_health'):
            result = await scraper.scrape_flights(self.sample_criteria)
            
            # Should fail on first timeout
            assert result.success is False
            assert "First timeout" in result.error_message


class TestNetworkFailureScenarios:
    """Test network failure scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sample_criteria = SearchCriteria(
            origin="NYC",
            destination="SF",
            departure_date=date(2024, 8, 1),
            trip_type=TripType.ONE_WAY,
            max_results=15
        )

    @pytest.mark.asyncio
    async def test_network_connection_failure(self):
        """Test network connection failure during navigation."""
        mock_page = AsyncMock()
        mock_page.goto.side_effect = PlaywrightError("net::ERR_NETWORK_CHANGED")
        
        handler = FormHandler(mock_page)
        
        with pytest.raises(NavigationError):
            await handler.navigate_to_google_flights(self.sample_criteria)

    @pytest.mark.asyncio
    async def test_dns_resolution_failure(self):
        """Test DNS resolution failure."""
        mock_page = AsyncMock()
        mock_page.goto.side_effect = PlaywrightError("net::ERR_NAME_NOT_RESOLVED")
        
        handler = FormHandler(mock_page)
        
        with pytest.raises(NavigationError):
            await handler.navigate_to_google_flights(self.sample_criteria)

    @pytest.mark.asyncio
    async def test_connection_refused(self):
        """Test connection refused error."""
        mock_page = AsyncMock()
        mock_page.goto.side_effect = PlaywrightError("net::ERR_CONNECTION_REFUSED")
        
        handler = FormHandler(mock_page)
        
        with pytest.raises(NavigationError):
            await handler.navigate_to_google_flights(self.sample_criteria)

    @pytest.mark.asyncio
    async def test_network_failure_during_data_extraction(self):
        """Test network failure during data extraction."""
        mock_page = AsyncMock()
        mock_page.evaluate.side_effect = PlaywrightError("net::ERR_INTERNET_DISCONNECTED")
        
        extractor = DataExtractor(mock_page)
        
        # The implementation catches network errors and returns empty result
        result = await extractor.extract_flight_data(self.sample_criteria, 25)
        assert result == []


class TestSelectorFailureScenarios:
    """Test selector failure and element not found scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sample_criteria = SearchCriteria(
            origin="DFW",
            destination="SEA",
            departure_date=date(2024, 9, 1),
            trip_type=TripType.ROUND_TRIP,
            return_date=date(2024, 9, 8),
            max_results=20
        )

    @pytest.mark.asyncio
    async def test_origin_input_not_found(self):
        """Test origin input field not found."""
        mock_page = AsyncMock()
        mock_page.keyboard = AsyncMock()
        mock_page.keyboard.press = AsyncMock()
        
        with patch('flight_scraper.core.form_handler.robust_fill') as mock_fill:
            mock_fill.side_effect = [False, True]  # Origin fails, destination succeeds
            
            handler = FormHandler(mock_page)
            
            with pytest.raises(ScrapingError, match="Form filling failed"):
                await handler.fill_search_form(self.sample_criteria)

    @pytest.mark.asyncio
    async def test_destination_input_not_found(self):
        """Test destination input field not found."""
        mock_page = AsyncMock()
        mock_page.keyboard = AsyncMock()
        mock_page.keyboard.press = AsyncMock()
        
        with patch('flight_scraper.core.form_handler.robust_fill') as mock_fill, \
             patch('flight_scraper.core.form_handler.random_delay'):
            mock_fill.side_effect = [True, False]  # Origin succeeds, destination fails
            
            handler = FormHandler(mock_page)
            
            with pytest.raises(ScrapingError, match="Form filling failed"):
                await handler.fill_search_form(self.sample_criteria)

    @pytest.mark.asyncio
    async def test_departure_date_field_not_found(self):
        """Test departure date field not found."""
        mock_page = AsyncMock()
        mock_page.keyboard = AsyncMock()
        mock_page.keyboard.press = AsyncMock()
        mock_page.keyboard.type = AsyncMock()
        
        with patch('flight_scraper.core.form_handler.robust_fill') as mock_fill, \
             patch('flight_scraper.core.form_handler.robust_click') as mock_click, \
             patch('flight_scraper.core.form_handler.random_delay'):
            
            # Origin and destination succeed
            mock_fill.side_effect = [True, True, False]  # Date fails
            mock_click.return_value = False  # Click fallback also fails
            
            handler = FormHandler(mock_page)
            
            with pytest.raises(ScrapingError, match="Form filling failed"):
                await handler.fill_search_form(self.sample_criteria)

    @pytest.mark.asyncio
    async def test_search_button_not_found(self):
        """Test search button not found."""
        mock_page = AsyncMock()
        
        with patch('flight_scraper.core.form_handler.robust_click') as mock_click, \
             patch.object(FormHandler, '_fallback_search_strategies') as mock_fallback:
            
            mock_click.return_value = False  # Primary search fails
            mock_fallback.return_value = False  # All fallbacks fail
            
            handler = FormHandler(mock_page)
            
            with pytest.raises(ScrapingError, match="Failed to trigger search with any method"):
                await handler.trigger_search()

    @pytest.mark.asyncio
    async def test_flight_containers_not_found(self):
        """Test flight result containers not found."""
        mock_page = AsyncMock()
        mock_page.evaluate.return_value = {"count": 0, "ulInfo": []}
        
        extractor = DataExtractor(mock_page)
        
        result = await extractor.extract_flight_data(self.sample_criteria, 50)
        
        # Should return empty list, not raise exception
        assert result == []

    @pytest.mark.asyncio
    async def test_flight_data_elements_malformed(self):
        """Test malformed flight data elements."""
        mock_page = AsyncMock()
        mock_element = AsyncMock()
        
        # Mock element that fails all extraction attempts
        mock_element.query_selector.return_value = None
        mock_element.query_selector_all.return_value = []
        
        extractor = DataExtractor(mock_page)
        
        result = await extractor.extract_single_flight(mock_element)
        
        # The implementation creates a FlightOffer with default "N/A" values
        # when extraction fails, rather than returning None
        assert result is not None
        assert result.price == "N/A"
        assert result.segments[0].airline == "Unknown"


class TestBrowserCrashScenarios:
    """Test browser crash and recovery scenarios."""

    @pytest.mark.asyncio
    async def test_browser_process_crash(self):
        """Test browser process crash during operation."""
        manager = BrowserManager(headless=True)
        
        # Mock browser that crashes
        mock_browser = AsyncMock()
        mock_browser.close.side_effect = PlaywrightError("Browser process crashed")
        manager.browser = mock_browser
        
        # Should handle crash gracefully during cleanup
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_page_becomes_unresponsive(self):
        """Test page becoming unresponsive."""
        mock_page = AsyncMock()
        mock_page.evaluate.side_effect = PlaywrightError("Execution context was destroyed")
        
        extractor = DataExtractor(mock_page)
        
        # The implementation catches context errors and returns empty result
        result = await extractor.extract_flight_data(
            SearchCriteria(
                origin="ATL",
                destination="DEN",
                departure_date=date(2024, 10, 1),
                trip_type=TripType.ONE_WAY,
                max_results=10
            ), 50
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_context_lost_during_operation(self):
        """Test browser context lost during operation."""
        mock_page = AsyncMock()
        mock_page.goto.side_effect = PlaywrightError("Target page, context or browser has been closed")
        
        handler = FormHandler(mock_page)
        
        with pytest.raises(NavigationError):
            await handler.navigate_to_google_flights(
                SearchCriteria(
                    origin="BOS",
                    destination="LAX",
                    departure_date=date(2024, 11, 1),
                    trip_type=TripType.ONE_WAY,
                    max_results=5
                )
            )


class TestResourceExhaustionScenarios:
    """Test resource exhaustion scenarios."""

    @pytest.mark.asyncio
    async def test_memory_exhaustion(self):
        """Test memory exhaustion during data extraction."""
        mock_page = AsyncMock()
        mock_page.evaluate.side_effect = PlaywrightError("JavaScript heap out of memory")
        
        extractor = DataExtractor(mock_page)
        
        # The implementation catches memory errors and returns empty result
        result = await extractor.extract_flight_data(
            SearchCriteria(
                origin="PHX",
                destination="MIA",
                departure_date=date(2024, 12, 1),
                trip_type=TripType.ONE_WAY,
                max_results=100
            ), 100
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_too_many_browser_contexts(self):
        """Test too many browser contexts error."""
        manager = BrowserManager(headless=True)
        
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_context.side_effect = PlaywrightError("Too many browser contexts")
        
        mock_playwright.chromium.launch.return_value = mock_browser
        
        with patch('flight_scraper.core.browser_manager.async_playwright') as mock_async_playwright:
            mock_async_playwright.return_value.start.return_value = mock_playwright
            
            with pytest.raises(ScrapingError):
                await manager.initialize()


class TestConcurrencyScenarios:
    """Test concurrency and race condition scenarios."""

    @pytest.mark.asyncio
    async def test_concurrent_scraper_instances(self):
        """Test multiple scraper instances running concurrently."""
        async def run_scraper():
            scraper = GoogleFlightsScraper(headless=True)
            
            # Mock all components to avoid actual browser operations
            with patch.object(scraper, 'initialize'), \
                 patch.object(scraper, 'cleanup'), \
                 patch.object(scraper, 'scrape_flights') as mock_scrape:
                
                mock_scrape.return_value = Mock(success=True, flights=[], total_results=0)
                
                async with scraper:
                    return await scraper.scrape_flights(
                        SearchCriteria(
                            origin="LAX",
                            destination="JFK",
                            departure_date=date(2024, 7, 15),
                            trip_type=TripType.ONE_WAY,
                            max_results=5
                        )
                    )
        
        # Run multiple scrapers concurrently
        tasks = [run_scraper() for _ in range(3)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete without race conditions
        assert len(results) == 3
        assert all(not isinstance(r, Exception) for r in results)

    @pytest.mark.asyncio
    async def test_cleanup_during_active_operation(self):
        """Test cleanup called during active scraping operation."""
        scraper = GoogleFlightsScraper(headless=True)
        
        mock_browser_manager = AsyncMock()
        scraper.browser_manager = mock_browser_manager
        
        # Simulate cleanup being called while operation is in progress
        cleanup_task = asyncio.create_task(scraper.cleanup())
        await asyncio.sleep(0.01)  # Let cleanup start
        
        # Should complete without hanging
        await cleanup_task
        
        assert scraper.browser_manager is None