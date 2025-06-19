"""Comprehensive unit tests for flight scraper utilities."""

import time
from datetime import date
from unittest.mock import AsyncMock, Mock, patch

import pytest
from playwright.async_api import ElementHandle, Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from flight_scraper.core.models import SelectorFailureType, SelectorMonitoring, SelectorStrategy
from flight_scraper.utils import (
    ROBUST_SELECTOR_CONFIGS,
    RobustSelector,
    SelectorHealthMonitor,
    format_date_for_input,
    parse_duration,
    parse_price,
    parse_stops,
    random_delay,
    retry_async_operation,
    robust_click,
    robust_fill,
    robust_find_element,
    robust_get_text,
    safe_click,
    safe_fill,
    safe_get_text,
    setup_logging,
    wait_for_element,
)


class TestBasicUtilities:
    """Test basic utility functions."""

    def test_parse_duration(self):
        """Test duration parsing."""
        assert parse_duration("5h 30m") == "5h 30m"
        assert parse_duration("2 hr 15 min") == "2 hr 15 min"
        assert parse_duration("") == "Unknown"
        assert parse_duration(None) == "Unknown"
        assert parse_duration("0h 0m") == "0h 0m"
        assert parse_duration("24h 59m") == "24h 59m"
        assert parse_duration("1h") == "1h"
        assert parse_duration("30m") == "30m"
        # Test special characters removal
        assert parse_duration("5h!30m@") == "5h30m"

    def test_parse_price(self):
        """Test price parsing."""
        assert parse_price("$350") == "$350"
        assert parse_price("$1,250") == "$1,250"
        assert parse_price("350") == "350"
        assert parse_price("") == "0"
        assert parse_price(None) == "0"
        assert parse_price("$0") == "$0"
        assert parse_price("$10,000") == "$10,000"
        assert parse_price("USD 500") == "500"
        assert parse_price("€250") == "€250"
        assert parse_price("£1,500") == "£1,500"
        assert parse_price("¥5000") == "¥5000"

    def test_parse_stops(self):
        """Test stops parsing."""
        assert parse_stops("nonstop") == 0
        assert parse_stops("direct") == 0
        assert parse_stops("1 stop") == 1
        assert parse_stops("2 stops") == 2
        assert parse_stops("") == 0
        assert parse_stops(None) == 0
        assert parse_stops("NONSTOP") == 0
        assert parse_stops("3 stops") == 3
        assert parse_stops("multiple stops") == 1
        assert (
            parse_stops("Non-stop flight") == 1
        )  # Returns 1 because it finds the number "1" in "Non-stop"
        assert parse_stops("Direct flight") == 0  # Contains "direct"

    def test_format_date_for_input(self):
        """Test date formatting."""
        test_date = date(2025, 7, 1)
        formatted = format_date_for_input(test_date)
        assert formatted == "2025-07-01"

        # Test different dates
        assert format_date_for_input(date(2024, 12, 31)) == "2024-12-31"
        assert format_date_for_input(date(2023, 1, 1)) == "2023-01-01"


class TestAsyncUtilities:
    """Test async utility functions."""

    @pytest.mark.asyncio
    async def test_random_delay(self):
        """Test random delay function."""
        start_time = time.time()
        await random_delay(0.1, 0.2)
        elapsed = time.time() - start_time
        assert 0.08 <= elapsed <= 0.25  # Allow some tolerance

    @pytest.mark.asyncio
    async def test_random_delay_default_config(self):
        """Test random delay with default config."""
        with patch("flight_scraper.utils.SCRAPER_CONFIG", {"delay_range": (0.1, 0.2)}):
            start_time = time.time()
            await random_delay()
            elapsed = time.time() - start_time
            assert 0.08 <= elapsed <= 0.25

    @pytest.mark.asyncio
    async def test_wait_for_element_success(self):
        """Test successful element waiting."""
        mock_page = AsyncMock(spec=Page)
        mock_page.wait_for_selector.return_value = None

        result = await wait_for_element(mock_page, ".test-selector")
        assert result is True
        mock_page.wait_for_selector.assert_called_once_with(".test-selector", timeout=10000)

    @pytest.mark.asyncio
    async def test_wait_for_element_timeout(self):
        """Test element waiting timeout."""
        mock_page = AsyncMock(spec=Page)
        mock_page.wait_for_selector.side_effect = PlaywrightTimeoutError("Timeout")

        result = await wait_for_element(mock_page, ".test-selector", timeout=5000)
        assert result is False

    @pytest.mark.asyncio
    async def test_safe_click_success(self):
        """Test successful safe click."""
        mock_page = AsyncMock(spec=Page)
        mock_page.wait_for_selector.return_value = None
        mock_page.click.return_value = None

        with patch("flight_scraper.utils.random_delay"):
            result = await safe_click(mock_page, ".test-button")
            assert result is True
            mock_page.click.assert_called_once_with(".test-button")

    @pytest.mark.asyncio
    async def test_safe_click_timeout(self):
        """Test safe click timeout."""
        mock_page = AsyncMock(spec=Page)
        mock_page.wait_for_selector.side_effect = PlaywrightTimeoutError("Timeout")

        result = await safe_click(mock_page, ".test-button")
        assert result is False

    @pytest.mark.asyncio
    async def test_safe_click_error(self):
        """Test safe click with other error."""
        mock_page = AsyncMock(spec=Page)
        mock_page.wait_for_selector.return_value = None
        mock_page.click.side_effect = Exception("Click failed")

        result = await safe_click(mock_page, ".test-button")
        assert result is False

    @pytest.mark.asyncio
    async def test_safe_fill_success(self):
        """Test successful safe fill."""
        mock_page = AsyncMock(spec=Page)
        mock_page.wait_for_selector.return_value = None
        mock_page.fill.return_value = None

        with patch("flight_scraper.utils.random_delay"):
            result = await safe_fill(mock_page, ".test-input", "test value")
            assert result is True
            mock_page.fill.assert_called_once_with(".test-input", "test value")

    @pytest.mark.asyncio
    async def test_safe_fill_timeout(self):
        """Test safe fill timeout."""
        mock_page = AsyncMock(spec=Page)
        mock_page.wait_for_selector.side_effect = PlaywrightTimeoutError("Timeout")

        result = await safe_fill(mock_page, ".test-input", "test value")
        assert result is False

    @pytest.mark.asyncio
    async def test_safe_fill_error(self):
        """Test safe fill with other error."""
        mock_page = AsyncMock(spec=Page)
        mock_page.wait_for_selector.return_value = None
        mock_page.fill.side_effect = Exception("Fill failed")

        result = await safe_fill(mock_page, ".test-input", "test value")
        assert result is False

    @pytest.mark.asyncio
    async def test_safe_get_text_success(self):
        """Test successful text extraction."""
        mock_page = AsyncMock(spec=Page)
        mock_element = AsyncMock(spec=ElementHandle)
        mock_element.inner_text.return_value = "  test text  "

        mock_page.wait_for_selector.return_value = None
        mock_page.query_selector.return_value = mock_element

        result = await safe_get_text(mock_page, ".test-element")
        assert result == "test text"

    @pytest.mark.asyncio
    async def test_safe_get_text_no_element(self):
        """Test text extraction with no element found."""
        mock_page = AsyncMock(spec=Page)
        mock_page.wait_for_selector.return_value = None
        mock_page.query_selector.return_value = None

        result = await safe_get_text(mock_page, ".test-element")
        assert result is None

    @pytest.mark.asyncio
    async def test_safe_get_text_empty_text(self):
        """Test text extraction with empty text."""
        mock_page = AsyncMock(spec=Page)
        mock_element = AsyncMock(spec=ElementHandle)
        mock_element.inner_text.return_value = ""

        mock_page.wait_for_selector.return_value = None
        mock_page.query_selector.return_value = mock_element

        result = await safe_get_text(mock_page, ".test-element")
        assert result is None

    @pytest.mark.asyncio
    async def test_safe_get_text_timeout(self):
        """Test text extraction timeout."""
        mock_page = AsyncMock(spec=Page)
        mock_page.wait_for_selector.side_effect = PlaywrightTimeoutError("Timeout")

        result = await safe_get_text(mock_page, ".test-element")
        assert result is None

    @pytest.mark.asyncio
    async def test_safe_get_text_error(self):
        """Test text extraction with other error."""
        mock_page = AsyncMock(spec=Page)
        mock_page.wait_for_selector.return_value = None
        mock_page.query_selector.side_effect = Exception("Query failed")

        result = await safe_get_text(mock_page, ".test-element")
        assert result is None

    @pytest.mark.asyncio
    async def test_retry_async_operation_success_first_try(self):
        """Test successful retry operation on first try."""

        async def test_operation():
            return "success"

        result = await retry_async_operation(test_operation, max_attempts=3, delay=0.01)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_async_operation_success_after_retry(self):
        """Test successful retry operation after failure."""
        call_count = 0

        async def test_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("First attempt failed")
            return "success"

        result = await retry_async_operation(test_operation, max_attempts=3, delay=0.01)
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_async_operation_all_fail(self):
        """Test retry operation when all attempts fail."""

        async def test_operation():
            raise Exception("Always fails")

        with pytest.raises(Exception, match="Always fails"):
            await retry_async_operation(test_operation, max_attempts=2, delay=0.01)

    @pytest.mark.asyncio
    async def test_retry_async_operation_no_exponential_backoff(self):
        """Test retry with fixed delay."""
        call_times = []

        async def test_operation():
            call_times.append(time.time())
            raise Exception("Fail")

        with pytest.raises(Exception):
            await retry_async_operation(
                test_operation, max_attempts=3, delay=0.01, exponential_backoff=False
            )

        assert len(call_times) == 3


class TestRobustSelector:
    """Test robust selector functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_page = AsyncMock(spec=Page)
        self.selector = RobustSelector("test_element", self.mock_page)

    @pytest.mark.asyncio
    async def test_find_element_success_semantic(self):
        """Test successful element finding with semantic strategy."""
        mock_element = AsyncMock(spec=ElementHandle)
        mock_element.is_visible.return_value = True
        mock_element.is_enabled.return_value = True

        self.mock_page.wait_for_selector.return_value = None
        self.mock_page.query_selector.return_value = mock_element

        config = {"semantic": [".test-selector"]}

        result = await self.selector.find_element(config, timeout=1000)
        assert result == mock_element
        assert self.selector.monitoring.final_success is True
        assert self.selector.monitoring.successful_strategy == SelectorStrategy.SEMANTIC

    @pytest.mark.asyncio
    async def test_find_element_fallback_to_structural(self):
        """Test fallback from semantic to structural strategy."""
        mock_element = AsyncMock(spec=ElementHandle)
        mock_element.is_visible.return_value = True
        mock_element.is_enabled.return_value = True

        # First call (semantic) fails, second call (structural) succeeds
        self.mock_page.wait_for_selector.side_effect = [
            PlaywrightTimeoutError("Timeout"),  # Semantic fails
            None,  # Structural succeeds
        ]
        self.mock_page.query_selector.return_value = mock_element
        self.mock_page.evaluate.return_value = None  # For DOM context

        config = {"semantic": [".semantic-selector"], "structural": [".structural-selector"]}

        result = await self.selector.find_element(config, timeout=1000)
        assert result == mock_element
        assert self.selector.monitoring.final_success is True
        assert self.selector.monitoring.successful_strategy == SelectorStrategy.STRUCTURAL

    @pytest.mark.asyncio
    async def test_find_element_not_interactable(self):
        """Test element found but not interactable."""
        mock_element = AsyncMock(spec=ElementHandle)
        mock_element.is_visible.return_value = False
        mock_element.is_enabled.return_value = True

        self.mock_page.wait_for_selector.return_value = None
        self.mock_page.query_selector.return_value = mock_element
        self.mock_page.evaluate.return_value = None

        config = {"semantic": [".test-selector"]}

        result = await self.selector.find_element(config, timeout=1000)
        assert result is None
        assert self.selector.monitoring.final_success is False

    @pytest.mark.asyncio
    async def test_find_element_all_strategies_fail(self):
        """Test when all selector strategies fail."""
        self.mock_page.wait_for_selector.side_effect = PlaywrightTimeoutError("Timeout")
        self.mock_page.evaluate.return_value = None

        config = {
            "semantic": [".semantic-1", ".semantic-2"],
            "structural": [".structural-1"],
            "class_based": [".class-1"],
            "content_based": [".content-1"],
        }

        result = await self.selector.find_element(config, timeout=1000)
        assert result is None
        assert self.selector.monitoring.final_success is False
        assert self.selector.monitoring.total_attempts > 0

    def test_categorize_failure_types(self):
        """Test failure categorization for different error types."""
        # Test timeout error
        timeout_error = Exception("timeout occurred")
        assert self.selector._categorize_failure(timeout_error) == SelectorFailureType.NOT_FOUND

        # Test not found error
        not_found_error = Exception("element not found")
        assert self.selector._categorize_failure(not_found_error) == SelectorFailureType.NOT_FOUND

        # Test interaction error
        interaction_error = Exception("not interactable")
        assert (
            self.selector._categorize_failure(interaction_error)
            == SelectorFailureType.UNINTERACTABLE
        )

        # Test visibility error
        visibility_error = Exception("not visible")
        assert (
            self.selector._categorize_failure(visibility_error)
            == SelectorFailureType.UNINTERACTABLE
        )

        # Test enabled error
        enabled_error = Exception("not enabled")
        assert (
            self.selector._categorize_failure(enabled_error) == SelectorFailureType.UNINTERACTABLE
        )

        # Test stale element error
        stale_error = Exception("stale element reference")
        assert self.selector._categorize_failure(stale_error) == SelectorFailureType.STALE_ELEMENT

        # Test detached error
        detached_error = Exception("element is detached")
        assert (
            self.selector._categorize_failure(detached_error) == SelectorFailureType.STALE_ELEMENT
        )

        # Test permission error
        permission_error = Exception("permission denied")
        assert (
            self.selector._categorize_failure(permission_error)
            == SelectorFailureType.PERMISSION_DENIED
        )

        # Test generic error
        generic_error = Exception("something else happened")
        assert (
            self.selector._categorize_failure(generic_error)
            == SelectorFailureType.STRUCTURE_CHANGED
        )

    @pytest.mark.asyncio
    async def test_get_dom_context_success(self):
        """Test DOM context extraction for successful case."""
        self.mock_page.evaluate.return_value = "<div>test element</div>"

        context = await self.selector._get_dom_context(".test-selector")
        assert context == "<div>test element</div>"

    @pytest.mark.asyncio
    async def test_get_dom_context_error(self):
        """Test DOM context extraction with error."""
        self.mock_page.evaluate.side_effect = Exception("Evaluate failed")

        context = await self.selector._get_dom_context(".test-selector")
        assert context is None

    def test_record_attempt(self):
        """Test attempt recording functionality."""
        self.selector._record_attempt(
            selector=".test",
            strategy=SelectorStrategy.SEMANTIC,
            success=True,
            failure_type=None,
            error_message=None,
            execution_time=0.5,
        )

        assert len(self.selector.monitoring.attempts) == 1
        attempt = self.selector.monitoring.attempts[0]
        assert attempt.selector == ".test"
        assert attempt.strategy == SelectorStrategy.SEMANTIC
        assert attempt.success is True
        assert attempt.execution_time == 0.5


class TestSelectorHealthMonitor:
    """Test selector health monitoring functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = SelectorHealthMonitor()

    def test_record_page_health_success(self):
        """Test recording page health with successful selectors."""
        monitoring1 = SelectorMonitoring(element_type="element1")
        monitoring1.final_success = True
        monitoring2 = SelectorMonitoring(element_type="element2")
        monitoring2.final_success = True

        mock_monitoring = {"element1": monitoring1, "element2": monitoring2}

        self.monitor.record_page_health("test_page", mock_monitoring)

        assert "test_page" in self.monitor.page_health
        health = self.monitor.page_health["test_page"]
        assert health.overall_success_rate == 1.0
        assert len(health.critical_failures) == 0

    def test_record_page_health_mixed_results(self):
        """Test recording page health with mixed results."""
        monitoring1 = SelectorMonitoring(element_type="element1")
        monitoring1.final_success = True
        monitoring2 = SelectorMonitoring(element_type="element2")
        monitoring2.final_success = False
        monitoring3 = SelectorMonitoring(element_type="element3")
        monitoring3.final_success = True

        mock_monitoring = {
            "element1": monitoring1,
            "element2": monitoring2,
            "element3": monitoring3,
        }

        self.monitor.record_page_health("test_page", mock_monitoring)

        health = self.monitor.page_health["test_page"]
        assert abs(health.overall_success_rate - 0.667) < 0.01  # 2/3
        assert "element2" in health.critical_failures
        assert len(health.critical_failures) == 1

    def test_detect_structure_changes_true(self):
        """Test structure change detection when changes are present."""
        mock_monitoring = {
            "element1": Mock(
                final_success=False,
                total_attempts=3,
                attempts=[Mock(success=False, failure_type=SelectorFailureType.STRUCTURE_CHANGED)],
            ),
            "element2": Mock(
                final_success=False,
                total_attempts=4,
                attempts=[Mock(success=False, failure_type=SelectorFailureType.NOT_FOUND)],
            ),
        }

        result = self.monitor._detect_structure_changes(mock_monitoring)
        assert result is True

    def test_detect_structure_changes_false(self):
        """Test structure change detection when no changes are present."""
        mock_monitoring = {
            "element1": Mock(
                final_success=True,
                total_attempts=1,
                attempts=[Mock(success=True, failure_type=None)],
            ),
            "element2": Mock(
                final_success=False,
                total_attempts=2,
                attempts=[Mock(success=False, failure_type=SelectorFailureType.NOT_FOUND)],
            ),
        }

        result = self.monitor._detect_structure_changes(mock_monitoring)
        assert result is False

    def test_generate_alerts_critical(self):
        """Test alert generation for critical failures."""
        monitoring1 = SelectorMonitoring(element_type="element1")
        monitoring1.final_success = False
        monitoring2 = SelectorMonitoring(element_type="element2")
        monitoring2.final_success = False
        monitoring3 = SelectorMonitoring(element_type="element3")
        monitoring3.final_success = False

        mock_monitoring = {
            "element1": monitoring1,
            "element2": monitoring2,
            "element3": monitoring3,
        }

        with patch("time.time", return_value=1234567890):
            self.monitor.record_page_health("test_page", mock_monitoring)

        # Should generate alerts for low success rate
        assert "test_page" in self.monitor.failure_patterns
        alerts = self.monitor.failure_patterns["test_page"]
        assert len(alerts) > 0

        # Check for critical alert
        critical_alerts = [alert for alert in alerts if alert.severity == "critical"]
        assert len(critical_alerts) > 0

    def test_get_health_report_empty(self):
        """Test health report generation with no data."""
        report = self.monitor.get_health_report()

        assert "timestamp" in report
        assert "pages_monitored" in report
        assert "overall_health" in report
        assert "critical_issues" in report
        assert "recommendations" in report
        assert report["pages_monitored"] == 0

    def test_get_health_report_with_data(self):
        """Test health report generation with data."""
        monitoring1 = SelectorMonitoring(element_type="element1")
        monitoring1.final_success = True

        mock_monitoring = {"element1": monitoring1}

        self.monitor.record_page_health("test_page1", mock_monitoring)
        self.monitor.record_page_health("test_page2", mock_monitoring)

        report = self.monitor.get_health_report()

        assert report["pages_monitored"] == 2
        assert "average_success_rate" in report["overall_health"]
        assert report["overall_health"]["average_success_rate"] == 1.0

    def test_get_health_report_with_issues(self):
        """Test health report generation with critical issues."""
        # Create page with structure changes
        monitoring1 = SelectorMonitoring(element_type="element1")
        monitoring1.final_success = False

        mock_monitoring = {"element1": monitoring1}

        # Mock structure change detection
        with patch.object(self.monitor, "_detect_structure_changes", return_value=True):
            self.monitor.record_page_health("problem_page", mock_monitoring)

        report = self.monitor.get_health_report()

        assert len(report["critical_issues"]) > 0
        assert any("Structure changes detected" in issue for issue in report["critical_issues"])

    def test_get_health_report_with_recommendations(self):
        """Test health report generation with recommendations."""
        monitoring1 = SelectorMonitoring(element_type="element1")
        monitoring1.final_success = False
        monitoring2 = SelectorMonitoring(element_type="element2")
        monitoring2.final_success = False

        mock_monitoring = {"element1": monitoring1, "element2": monitoring2}

        self.monitor.record_page_health("low_success_page", mock_monitoring)

        report = self.monitor.get_health_report()

        # Should generate recommendations for low success rate
        assert len(report["recommendations"]) > 0
        assert any(
            "updating selector configurations" in rec.lower() for rec in report["recommendations"]
        )


class TestRobustSelectorFunctions:
    """Test high-level robust selector functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_page = AsyncMock(spec=Page)

    @pytest.mark.asyncio
    async def test_robust_find_element_success(self):
        """Test robust element finding with valid element type."""
        mock_element = AsyncMock(spec=ElementHandle)
        mock_element.is_visible.return_value = True
        mock_element.is_enabled.return_value = True

        self.mock_page.wait_for_selector.return_value = None
        self.mock_page.query_selector.return_value = mock_element

        result = await robust_find_element(self.mock_page, "origin_input")
        assert result == mock_element

    @pytest.mark.asyncio
    async def test_robust_find_element_unknown_type(self):
        """Test robust finding with unknown element type."""
        result = await robust_find_element(self.mock_page, "unknown_element")
        assert result is None

    @pytest.mark.asyncio
    async def test_robust_click_success(self):
        """Test robust clicking with success."""
        mock_element = AsyncMock(spec=ElementHandle)
        mock_element.is_visible.return_value = True
        mock_element.is_enabled.return_value = True
        mock_element.click.return_value = None

        self.mock_page.wait_for_selector.return_value = None
        self.mock_page.query_selector.return_value = mock_element

        with patch("flight_scraper.utils.random_delay"):
            result = await robust_click(self.mock_page, "search_button")
            assert result is True

    @pytest.mark.asyncio
    async def test_robust_click_element_not_found(self):
        """Test robust clicking when element not found."""
        self.mock_page.wait_for_selector.side_effect = PlaywrightTimeoutError("Timeout")
        self.mock_page.evaluate.return_value = None

        result = await robust_click(self.mock_page, "search_button")
        assert result is False

    @pytest.mark.asyncio
    async def test_robust_click_click_error(self):
        """Test robust clicking when click fails."""
        mock_element = AsyncMock(spec=ElementHandle)
        mock_element.is_visible.return_value = True
        mock_element.is_enabled.return_value = True
        mock_element.click.side_effect = Exception("Click failed")

        self.mock_page.wait_for_selector.return_value = None
        self.mock_page.query_selector.return_value = mock_element

        result = await robust_click(self.mock_page, "search_button")
        assert result is False

    @pytest.mark.asyncio
    async def test_robust_fill_success(self):
        """Test robust filling with success."""
        mock_element = AsyncMock(spec=ElementHandle)
        mock_element.is_visible.return_value = True
        mock_element.is_enabled.return_value = True
        mock_element.fill.return_value = None

        self.mock_page.wait_for_selector.return_value = None
        self.mock_page.query_selector.return_value = mock_element

        with patch("flight_scraper.utils.random_delay"):
            result = await robust_fill(self.mock_page, "origin_input", "JFK")
            assert result is True

    @pytest.mark.asyncio
    async def test_robust_fill_element_not_found(self):
        """Test robust filling when element not found."""
        self.mock_page.wait_for_selector.side_effect = PlaywrightTimeoutError("Timeout")
        self.mock_page.evaluate.return_value = None

        result = await robust_fill(self.mock_page, "origin_input", "JFK")
        assert result is False

    @pytest.mark.asyncio
    async def test_robust_fill_fill_error(self):
        """Test robust filling when fill fails."""
        mock_element = AsyncMock(spec=ElementHandle)
        mock_element.is_visible.return_value = True
        mock_element.is_enabled.return_value = True
        mock_element.fill.side_effect = Exception("Fill failed")

        self.mock_page.wait_for_selector.return_value = None
        self.mock_page.query_selector.return_value = mock_element

        result = await robust_fill(self.mock_page, "origin_input", "JFK")
        assert result is False

    @pytest.mark.asyncio
    async def test_robust_get_text_success(self):
        """Test robust text getting with success."""
        mock_element = AsyncMock(spec=ElementHandle)
        mock_element.is_visible.return_value = True
        mock_element.is_enabled.return_value = True
        mock_element.inner_text.return_value = "test text"

        self.mock_page.wait_for_selector.return_value = None
        self.mock_page.query_selector.return_value = mock_element

        result = await robust_get_text(self.mock_page, "flight_results")
        assert result == "test text"

    @pytest.mark.asyncio
    async def test_robust_get_text_element_not_found(self):
        """Test robust text getting when element not found."""
        self.mock_page.wait_for_selector.side_effect = PlaywrightTimeoutError("Timeout")
        self.mock_page.evaluate.return_value = None

        result = await robust_get_text(self.mock_page, "flight_results")
        assert result is None

    @pytest.mark.asyncio
    async def test_robust_get_text_inner_text_error(self):
        """Test robust text getting when inner_text fails."""
        mock_element = AsyncMock(spec=ElementHandle)
        mock_element.is_visible.return_value = True
        mock_element.is_enabled.return_value = True
        mock_element.inner_text.side_effect = Exception("Inner text failed")

        self.mock_page.wait_for_selector.return_value = None
        self.mock_page.query_selector.return_value = mock_element

        result = await robust_get_text(self.mock_page, "flight_results")
        assert result is None


class TestSelectorConfigs:
    """Test selector configurations."""

    def test_robust_selector_configs_exist(self):
        """Test that all expected selector configs exist."""
        expected_elements = [
            "origin_input",
            "destination_input",
            "departure_date",
            "return_date",
            "search_button",
            "flight_results",
        ]

        for element in expected_elements:
            assert element in ROBUST_SELECTOR_CONFIGS
            config = ROBUST_SELECTOR_CONFIGS[element]
            assert "semantic" in config
            assert isinstance(config["semantic"], list)
            assert len(config["semantic"]) > 0

    def test_selector_configs_structure(self):
        """Test that selector configs have proper structure."""
        for element_name, config in ROBUST_SELECTOR_CONFIGS.items():
            # Check that config has strategy keys
            assert isinstance(config, dict)

            # Check semantic selectors exist and are non-empty
            assert "semantic" in config
            assert isinstance(config["semantic"], list)
            assert len(config["semantic"]) > 0

            # Check that all selectors are strings
            for strategy, selectors in config.items():
                assert isinstance(selectors, list)
                for selector in selectors:
                    assert isinstance(selector, str)
                    assert len(selector) > 0

    def test_setup_logging(self):
        """Test logging setup functionality."""
        with patch("flight_scraper.utils.logger") as mock_logger:
            with patch(
                "flight_scraper.core.config.LOG_CONFIG",
                {
                    "file": "test.log",
                    "level": "INFO",
                    "format": "{message}",
                    "rotation": "1 MB",
                    "retention": "1 day",
                },
            ):
                setup_logging()

                # Should remove existing handlers and add new ones
                mock_logger.remove.assert_called_once()
                assert mock_logger.add.call_count == 2
