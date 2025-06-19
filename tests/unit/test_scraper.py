"""Unit tests for main GoogleFlightsScraper component."""

from datetime import date
from unittest.mock import AsyncMock, Mock, patch

import pytest

from flight_scraper.core.browser_manager import BrowserManager
from flight_scraper.core.data_extractor import DataExtractor
from flight_scraper.core.form_handler import FormHandler
from flight_scraper.core.models import (
    FlightOffer,
    FlightSegment,
    ScrapingError,
    ScrapingResult,
    SearchCriteria,
    TripType,
)
from flight_scraper.core.scraper import GoogleFlightsScraper, scrape_flights_async


class TestGoogleFlightsScraper:
    """Test GoogleFlightsScraper main component."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scraper = GoogleFlightsScraper(headless=True)

        self.sample_criteria = SearchCriteria(
            origin="JFK",
            destination="LAX",
            departure_date=date(2024, 7, 15),
            trip_type=TripType.ONE_WAY,
            max_results=10,
        )

        self.sample_flights = [
            FlightOffer(
                price="$350",
                stops=0,
                total_duration="5h 30m",
                segments=[
                    FlightSegment(
                        airline="Delta",
                        departure_airport="JFK",
                        arrival_airport="LAX",
                        departure_time="10:00 AM",
                        arrival_time="3:30 PM",
                        duration="5h 30m",
                    )
                ],
            ),
            FlightOffer(
                price="$425",
                stops=1,
                total_duration="7h 15m",
                segments=[
                    FlightSegment(
                        airline="United",
                        departure_airport="JFK",
                        arrival_airport="LAX",
                        departure_time="2:00 PM",
                        arrival_time="9:15 PM",
                        duration="7h 15m",
                    )
                ],
            ),
        ]

    def test_init(self):
        """Test scraper initialization."""
        assert self.scraper.headless is True
        assert self.scraper.browser_manager is None
        assert self.scraper.form_handler is None
        assert self.scraper.data_extractor is None
        assert self.scraper.health_monitor is not None
        assert isinstance(self.scraper.selector_monitors, dict)

    def test_init_default_headless(self):
        """Test scraper default headless setting."""
        scraper = GoogleFlightsScraper()
        assert scraper.headless is False

    @pytest.mark.asyncio
    async def test_context_manager_success(self):
        """Test successful async context manager usage."""
        with (
            patch.object(self.scraper, "initialize") as mock_init,
            patch.object(self.scraper, "cleanup") as mock_cleanup,
        ):

            mock_init.return_value = None
            mock_cleanup.return_value = None

            async with self.scraper as scraper:
                assert scraper is self.scraper

            mock_init.assert_called_once()
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_init_failure(self):
        """Test context manager with initialization failure."""
        with (
            patch.object(self.scraper, "initialize") as mock_init,
            patch.object(self.scraper, "cleanup") as mock_cleanup,
        ):

            mock_init.side_effect = ScrapingError("Init failed")
            mock_cleanup.return_value = None

            with pytest.raises(ScrapingError, match="Init failed"):
                async with self.scraper:
                    pass

            mock_init.assert_called_once()
            # __aexit__ is NOT called when __aenter__ raises an exception
            # This is the correct Python async context manager behavior
            mock_cleanup.assert_not_called()

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful scraper initialization."""
        mock_browser_manager = AsyncMock(spec=BrowserManager)
        mock_page = Mock()
        mock_browser_manager.get_page.return_value = mock_page

        with (
            patch("flight_scraper.core.scraper.BrowserManager") as MockBrowserManager,
            patch("flight_scraper.core.scraper.FormHandler") as MockFormHandler,
            patch("flight_scraper.core.scraper.DataExtractor") as MockDataExtractor,
        ):

            MockBrowserManager.return_value = mock_browser_manager
            mock_form_handler = Mock()
            mock_data_extractor = Mock()
            MockFormHandler.return_value = mock_form_handler
            MockDataExtractor.return_value = mock_data_extractor

            await self.scraper.initialize()

            assert self.scraper.browser_manager == mock_browser_manager
            assert self.scraper.form_handler == mock_form_handler
            assert self.scraper.data_extractor == mock_data_extractor

            MockBrowserManager.assert_called_once_with(headless=True)
            mock_browser_manager.initialize.assert_called_once()
            MockFormHandler.assert_called_once_with(mock_page)
            MockDataExtractor.assert_called_once_with(mock_page)

    @pytest.mark.asyncio
    async def test_initialize_browser_failure(self):
        """Test initialization with browser failure."""
        with (
            patch("flight_scraper.core.scraper.BrowserManager") as MockBrowserManager,
            patch.object(self.scraper, "cleanup") as mock_cleanup,
        ):

            mock_browser_manager = AsyncMock(spec=BrowserManager)
            mock_browser_manager.initialize.side_effect = Exception("Browser failed")
            MockBrowserManager.return_value = mock_browser_manager

            with pytest.raises(ScrapingError, match="Scraper initialization failed"):
                await self.scraper.initialize()

            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_success(self):
        """Test successful cleanup."""
        mock_browser_manager = AsyncMock(spec=BrowserManager)
        self.scraper.browser_manager = mock_browser_manager
        self.scraper.form_handler = Mock()
        self.scraper.data_extractor = Mock()

        await self.scraper.cleanup()

        assert self.scraper.browser_manager is None
        assert self.scraper.form_handler is None
        assert self.scraper.data_extractor is None
        mock_browser_manager.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_with_error(self):
        """Test cleanup with browser cleanup error."""
        mock_browser_manager = AsyncMock(spec=BrowserManager)
        mock_browser_manager.cleanup.side_effect = Exception("Cleanup failed")
        self.scraper.browser_manager = mock_browser_manager

        # Should not raise exception, just log error
        await self.scraper.cleanup()

        # The scraper should still clean up its references even if browser cleanup fails
        assert self.scraper.browser_manager is None

    @pytest.mark.asyncio
    async def test_scrape_flights_success(self):
        """Test successful flight scraping."""
        # Set up initialized components
        mock_browser_manager = Mock(spec=BrowserManager)
        mock_form_handler = AsyncMock(spec=FormHandler)
        mock_data_extractor = AsyncMock(spec=DataExtractor)

        self.scraper.browser_manager = mock_browser_manager
        self.scraper.form_handler = mock_form_handler
        self.scraper.data_extractor = mock_data_extractor

        mock_data_extractor.extract_flight_data.return_value = self.sample_flights

        with patch.object(self.scraper, "_record_session_health") as mock_record_health:
            mock_record_health.return_value = None

            result = await self.scraper.scrape_flights(self.sample_criteria)

            assert result.success is True
            assert len(result.flights) == 2
            assert result.total_results == 2
            assert result.search_criteria == self.sample_criteria
            assert result.execution_time >= 0
            assert result.error_message is None

            # Verify all phases were called
            mock_form_handler.navigate_to_google_flights.assert_called_once_with(
                self.sample_criteria
            )
            mock_form_handler.fill_search_form.assert_called_once_with(self.sample_criteria)
            mock_form_handler.trigger_search.assert_called_once()
            mock_data_extractor.extract_flight_data.assert_called_once_with(
                self.sample_criteria, self.sample_criteria.max_results
            )

    @pytest.mark.asyncio
    async def test_scrape_flights_not_initialized(self):
        """Test scraping when components not initialized."""
        with pytest.raises(ScrapingError, match="Scraper components not initialized"):
            await self.scraper.scrape_flights(self.sample_criteria)

    @pytest.mark.asyncio
    async def test_scrape_flights_navigation_failure(self):
        """Test scraping with navigation failure."""
        # Set up initialized components
        mock_browser_manager = Mock(spec=BrowserManager)
        mock_form_handler = AsyncMock(spec=FormHandler)
        mock_data_extractor = AsyncMock(spec=DataExtractor)

        self.scraper.browser_manager = mock_browser_manager
        self.scraper.form_handler = mock_form_handler
        self.scraper.data_extractor = mock_data_extractor

        mock_form_handler.navigate_to_google_flights.side_effect = Exception("Navigation failed")

        with patch.object(self.scraper, "_record_session_health") as mock_record_health:
            mock_record_health.return_value = None

            result = await self.scraper.scrape_flights(self.sample_criteria)

            assert result.success is False
            assert len(result.flights) == 0
            assert result.total_results == 0
            assert "Navigation failed" in result.error_message
            assert result.execution_time >= 0

    @pytest.mark.asyncio
    async def test_scrape_flights_form_filling_failure(self):
        """Test scraping with form filling failure."""
        mock_browser_manager = Mock(spec=BrowserManager)
        mock_form_handler = AsyncMock(spec=FormHandler)
        mock_data_extractor = AsyncMock(spec=DataExtractor)

        self.scraper.browser_manager = mock_browser_manager
        self.scraper.form_handler = mock_form_handler
        self.scraper.data_extractor = mock_data_extractor

        mock_form_handler.navigate_to_google_flights.return_value = None
        mock_form_handler.fill_search_form.side_effect = Exception("Form filling failed")

        with patch.object(self.scraper, "_record_session_health") as mock_record_health:
            mock_record_health.return_value = None

            result = await self.scraper.scrape_flights(self.sample_criteria)

            assert result.success is False
            assert "Form filling failed" in result.error_message

    @pytest.mark.asyncio
    async def test_scrape_flights_search_trigger_failure(self):
        """Test scraping with search trigger failure."""
        mock_browser_manager = Mock(spec=BrowserManager)
        mock_form_handler = AsyncMock(spec=FormHandler)
        mock_data_extractor = AsyncMock(spec=DataExtractor)

        self.scraper.browser_manager = mock_browser_manager
        self.scraper.form_handler = mock_form_handler
        self.scraper.data_extractor = mock_data_extractor

        mock_form_handler.navigate_to_google_flights.return_value = None
        mock_form_handler.fill_search_form.return_value = None
        mock_form_handler.trigger_search.side_effect = Exception("Search failed")

        with patch.object(self.scraper, "_record_session_health") as mock_record_health:
            mock_record_health.return_value = None

            result = await self.scraper.scrape_flights(self.sample_criteria)

            assert result.success is False
            assert "Search failed" in result.error_message

    @pytest.mark.asyncio
    async def test_scrape_flights_data_extraction_failure(self):
        """Test scraping with data extraction failure."""
        mock_browser_manager = Mock(spec=BrowserManager)
        mock_form_handler = AsyncMock(spec=FormHandler)
        mock_data_extractor = AsyncMock(spec=DataExtractor)

        self.scraper.browser_manager = mock_browser_manager
        self.scraper.form_handler = mock_form_handler
        self.scraper.data_extractor = mock_data_extractor

        mock_form_handler.navigate_to_google_flights.return_value = None
        mock_form_handler.fill_search_form.return_value = None
        mock_form_handler.trigger_search.return_value = None
        mock_data_extractor.extract_flight_data.side_effect = Exception("Extraction failed")

        with patch.object(self.scraper, "_record_session_health") as mock_record_health:
            mock_record_health.return_value = None

            result = await self.scraper.scrape_flights(self.sample_criteria)

            assert result.success is False
            assert "Extraction failed" in result.error_message

    @pytest.mark.asyncio
    async def test_record_session_health(self):
        """Test session health recording."""
        with patch.object(self.scraper.health_monitor, "record_page_health") as mock_record:
            await self.scraper._record_session_health("test_page")
            mock_record.assert_called_once_with("test_page", {})

    @pytest.mark.asyncio
    async def test_record_session_health_error(self):
        """Test session health recording with error."""
        with patch.object(self.scraper.health_monitor, "record_page_health") as mock_record:
            mock_record.side_effect = Exception("Health recording failed")

            # Should not raise exception, just log warning
            await self.scraper._record_session_health("test_page")

    def test_get_health_report(self):
        """Test health report retrieval."""
        mock_report = {"status": "healthy"}
        with patch.object(self.scraper.health_monitor, "get_health_report") as mock_get_report:
            mock_get_report.return_value = mock_report

            result = self.scraper.get_health_report()
            assert result == mock_report


class TestScrapeFlightsAsync:
    """Test the standalone scrape_flights_async function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sample_flights = [
            FlightOffer(
                price="$300",
                stops=0,
                total_duration="5h 00m",
                segments=[
                    FlightSegment(
                        airline="American",
                        departure_airport="NYC",
                        arrival_airport="SF",
                        departure_time="9:00 AM",
                        arrival_time="2:00 PM",
                        duration="5h 00m",
                    )
                ],
            )
        ]

    @pytest.mark.asyncio
    async def test_scrape_flights_async_one_way(self):
        """Test async scraping function for one-way trip."""
        mock_result = ScrapingResult(
            search_criteria=SearchCriteria(
                origin="NYC",
                destination="SF",
                departure_date=date(2024, 8, 15),
                trip_type=TripType.ONE_WAY,
                max_results=25,
            ),
            flights=self.sample_flights,
            total_results=1,
            success=True,
            execution_time=2.5,
        )

        with patch("flight_scraper.core.scraper.GoogleFlightsScraper") as MockScraper:
            mock_scraper_instance = AsyncMock()
            mock_scraper_instance.scrape_flights.return_value = mock_result
            MockScraper.return_value.__aenter__.return_value = mock_scraper_instance
            MockScraper.return_value.__aexit__.return_value = None

            result = await scrape_flights_async(
                origin="NYC",
                destination="SF",
                departure_date=date(2024, 8, 15),
                max_results=25,
                headless=False,
            )

            assert result.success is True
            assert len(result.flights) == 1
            assert result.flights[0].price == "$300"

            MockScraper.assert_called_once_with(headless=False)
            mock_scraper_instance.scrape_flights.assert_called_once()

            # Check criteria passed to scraper
            criteria = mock_scraper_instance.scrape_flights.call_args[0][0]
            assert criteria.origin == "NYC"
            assert criteria.destination == "SF"
            assert criteria.departure_date == date(2024, 8, 15)
            assert criteria.return_date is None
            assert criteria.trip_type == TripType.ONE_WAY
            assert criteria.max_results == 25

    @pytest.mark.asyncio
    async def test_scrape_flights_async_round_trip(self):
        """Test async scraping function for round-trip."""
        mock_result = ScrapingResult(
            search_criteria=SearchCriteria(
                origin="LAX",
                destination="JFK",
                departure_date=date(2024, 9, 1),
                return_date=date(2024, 9, 8),
                trip_type=TripType.ROUND_TRIP,
                max_results=50,
            ),
            flights=self.sample_flights,
            total_results=1,
            success=True,
            execution_time=3.2,
        )

        with patch("flight_scraper.core.scraper.GoogleFlightsScraper") as MockScraper:
            mock_scraper_instance = AsyncMock()
            mock_scraper_instance.scrape_flights.return_value = mock_result
            MockScraper.return_value.__aenter__.return_value = mock_scraper_instance
            MockScraper.return_value.__aexit__.return_value = None

            result = await scrape_flights_async(
                origin="LAX",
                destination="JFK",
                departure_date=date(2024, 9, 1),
                return_date=date(2024, 9, 8),
                max_results=50,
                headless=True,
            )

            assert result.success is True

            MockScraper.assert_called_once_with(headless=True)

            # Check criteria passed to scraper
            criteria = mock_scraper_instance.scrape_flights.call_args[0][0]
            assert criteria.origin == "LAX"
            assert criteria.destination == "JFK"
            assert criteria.departure_date == date(2024, 9, 1)
            assert criteria.return_date == date(2024, 9, 8)
            assert criteria.trip_type == TripType.ROUND_TRIP
            assert criteria.max_results == 50

    @pytest.mark.asyncio
    async def test_scrape_flights_async_default_params(self):
        """Test async scraping function with default parameters."""
        mock_result = ScrapingResult(
            search_criteria=SearchCriteria(
                origin="SEA",
                destination="MIA",
                departure_date=date(2024, 10, 1),
                trip_type=TripType.ONE_WAY,
                max_results=50,
            ),
            flights=[],
            total_results=0,
            success=True,
            execution_time=1.8,
        )

        with patch("flight_scraper.core.scraper.GoogleFlightsScraper") as MockScraper:
            mock_scraper_instance = AsyncMock()
            mock_scraper_instance.scrape_flights.return_value = mock_result
            MockScraper.return_value.__aenter__.return_value = mock_scraper_instance
            MockScraper.return_value.__aexit__.return_value = None

            result = await scrape_flights_async(
                origin="SEA",
                destination="MIA",
                departure_date=date(2024, 10, 1),
                # All other params use defaults
            )

            assert result.success is True

            MockScraper.assert_called_once_with(headless=False)  # Default headless=False

            # Check criteria with defaults
            criteria = mock_scraper_instance.scrape_flights.call_args[0][0]
            assert criteria.return_date is None
            assert criteria.trip_type == TripType.ONE_WAY
            assert criteria.max_results == 50

    @pytest.mark.asyncio
    async def test_scrape_flights_async_failure(self):
        """Test async scraping function with scraper failure."""
        with patch("flight_scraper.core.scraper.GoogleFlightsScraper") as MockScraper:
            mock_scraper_instance = AsyncMock()
            mock_scraper_instance.scrape_flights.side_effect = Exception("Scraper failed")
            MockScraper.return_value.__aenter__.return_value = mock_scraper_instance
            MockScraper.return_value.__aexit__.return_value = None

            with pytest.raises(Exception, match="Scraper failed"):
                await scrape_flights_async(
                    origin="DEN", destination="ATL", departure_date=date(2024, 11, 1)
                )
