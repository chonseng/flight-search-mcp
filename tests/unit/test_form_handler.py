"""Unit tests for FormHandler component."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import date
from playwright.async_api import Page

from flight_scraper.core.form_handler import FormHandler
from flight_scraper.core.models import SearchCriteria, TripType, NavigationError, ElementNotFoundError, ScrapingError


class TestFormHandler:
    """Test FormHandler component."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_page = AsyncMock(spec=Page)
        # Properly mock the keyboard object with all needed methods
        self.mock_page.keyboard = AsyncMock()
        self.mock_page.keyboard.press = AsyncMock()
        self.mock_page.keyboard.type = AsyncMock()
        self.handler = FormHandler(self.mock_page)
        
        self.sample_criteria = SearchCriteria(
            origin="JFK",
            destination="LAX",
            departure_date=date(2024, 7, 15),
            trip_type=TripType.ONE_WAY,
            max_results=10
        )
        
        self.round_trip_criteria = SearchCriteria(
            origin="NYC",
            destination="SF",
            departure_date=date(2024, 8, 1),
            return_date=date(2024, 8, 8),
            trip_type=TripType.ROUND_TRIP,
            max_results=15
        )

    def test_init(self):
        """Test FormHandler initialization."""
        assert self.handler.page == self.mock_page

    @pytest.mark.asyncio
    async def test_navigate_to_google_flights_one_way(self):
        """Test navigation to Google Flights for one-way trip."""
        self.mock_page.goto.return_value = None
        self.mock_page.url = "https://www.google.com/travel/flights"
        
        with patch('flight_scraper.core.form_handler.random_delay'):
            await self.handler.navigate_to_google_flights(self.sample_criteria)
        
        self.mock_page.goto.assert_called_once()
        call_args = self.mock_page.goto.call_args
        assert "google.com/travel/flights" in call_args[0][0]
        assert call_args.kwargs['wait_until'] == "domcontentloaded"

    @pytest.mark.asyncio
    async def test_navigate_to_google_flights_round_trip(self):
        """Test navigation to Google Flights for round-trip."""
        self.mock_page.goto.return_value = None
        self.mock_page.url = "https://www.google.com/travel/flights"
        
        with patch('flight_scraper.core.form_handler.random_delay'):
            await self.handler.navigate_to_google_flights(self.round_trip_criteria)
        
        self.mock_page.goto.assert_called_once()
        call_args = self.mock_page.goto.call_args
        # Should use round_trip URL for round trip searches
        assert "google.com/travel/flights" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_navigate_to_google_flights_fallback(self):
        """Test navigation with fallback URL on primary failure."""
        # First call fails, second succeeds
        self.mock_page.goto.side_effect = [Exception("Primary failed"), None]
        self.mock_page.url = "https://www.google.com/travel/flights"
        
        with patch('flight_scraper.core.form_handler.random_delay'):
            await self.handler.navigate_to_google_flights(self.sample_criteria)
        
        assert self.mock_page.goto.call_count == 2
        # Second call should be to fallback URL
        fallback_call = self.mock_page.goto.call_args_list[1]
        assert "https://www.google.com/travel/flights" in fallback_call[0][0]

    @pytest.mark.asyncio
    async def test_navigate_to_google_flights_both_fail(self):
        """Test navigation failure when both primary and fallback fail."""
        self.mock_page.goto.side_effect = Exception("Navigation failed")
        
        with patch('flight_scraper.core.form_handler.random_delay'):
            with pytest.raises(NavigationError, match="Navigation failed with both primary and fallback URLs"):
                await self.handler.navigate_to_google_flights(self.sample_criteria)

    @pytest.mark.asyncio
    async def test_fill_search_form_success(self):
        """Test successful form filling."""
        with patch('flight_scraper.core.form_handler.robust_fill') as mock_fill, \
             patch('flight_scraper.core.form_handler.random_delay'), \
             patch.object(self.handler, '_fill_departure_date') as mock_departure:
            
            mock_fill.return_value = True
            mock_departure.return_value = None
            
            await self.handler.fill_search_form(self.sample_criteria)
            
            # Should call robust_fill for origin and destination
            assert mock_fill.call_count == 2
            calls = mock_fill.call_args_list
            assert calls[0][0][1] == "origin_input"
            assert calls[0][0][2] == "JFK"
            assert calls[1][0][1] == "destination_input"
            assert calls[1][0][2] == "LAX"
            
            mock_departure.assert_called_once_with(self.sample_criteria.departure_date)

    @pytest.mark.asyncio
    async def test_fill_search_form_round_trip(self):
        """Test form filling for round-trip with return date."""
        with patch('flight_scraper.core.form_handler.robust_fill') as mock_fill, \
             patch('flight_scraper.core.form_handler.random_delay'), \
             patch.object(self.handler, '_fill_departure_date') as mock_departure, \
             patch.object(self.handler, '_fill_return_date') as mock_return:
            
            mock_fill.return_value = True
            mock_departure.return_value = None
            mock_return.return_value = None
            
            await self.handler.fill_search_form(self.round_trip_criteria)
            
            mock_departure.assert_called_once_with(self.round_trip_criteria.departure_date)
            mock_return.assert_called_once_with(self.round_trip_criteria.return_date)

    @pytest.mark.asyncio
    async def test_fill_search_form_origin_fail(self):
        """Test form filling when origin field fails."""
        with patch('flight_scraper.core.form_handler.robust_fill') as mock_fill, \
             patch('flight_scraper.core.form_handler.random_delay'):
            
            mock_fill.return_value = False
            
            with pytest.raises(ScrapingError, match="Form filling failed"):
                await self.handler.fill_search_form(self.sample_criteria)

    @pytest.mark.asyncio
    async def test_fill_search_form_destination_fail(self):
        """Test form filling when destination field fails."""
        with patch('flight_scraper.core.form_handler.robust_fill') as mock_fill, \
             patch('flight_scraper.core.form_handler.random_delay'):
            
            # Origin succeeds, destination fails
            mock_fill.side_effect = [True, False]
            
            with pytest.raises(ScrapingError, match="Form filling failed"):
                await self.handler.fill_search_form(self.sample_criteria)

    @pytest.mark.asyncio
    async def test_fill_departure_date_success(self):
        """Test successful departure date filling."""
        test_date = date(2024, 7, 15)
        
        with patch('flight_scraper.core.form_handler.robust_fill') as mock_fill, \
             patch('flight_scraper.core.form_handler.random_delay'):
            
            mock_fill.return_value = True
            
            await self.handler._fill_departure_date(test_date)
            
            mock_fill.assert_called_once()
            args = mock_fill.call_args[0]
            assert args[1] == "departure_date"
            assert args[2] == "2024-07-15"

    @pytest.mark.asyncio
    async def test_fill_departure_date_fallback(self):
        """Test departure date filling with click fallback."""
        test_date = date(2024, 7, 15)
        
        with patch('flight_scraper.core.form_handler.robust_fill') as mock_fill, \
             patch('flight_scraper.core.form_handler.robust_click') as mock_click, \
             patch('flight_scraper.core.form_handler.random_delay'):
            
            mock_fill.return_value = False
            mock_click.return_value = True
            
            await self.handler._fill_departure_date(test_date)
            
            mock_click.assert_called_once()
            self.mock_page.keyboard.type.assert_called_once_with("2024-07-15")

    @pytest.mark.asyncio
    async def test_fill_departure_date_all_fail(self):
        """Test departure date filling when all methods fail."""
        test_date = date(2024, 7, 15)
        
        with patch('flight_scraper.core.form_handler.robust_fill') as mock_fill, \
             patch('flight_scraper.core.form_handler.robust_click') as mock_click, \
             patch('flight_scraper.core.form_handler.random_delay'):
            
            mock_fill.return_value = False
            mock_click.return_value = False
            
            with pytest.raises(ElementNotFoundError, match="Could not find or interact with departure date field"):
                await self.handler._fill_departure_date(test_date)

    @pytest.mark.asyncio
    async def test_fill_return_date(self):
        """Test return date filling."""
        test_date = date(2024, 8, 8)
        
        with patch('flight_scraper.core.form_handler.robust_fill') as mock_fill, \
             patch('flight_scraper.core.form_handler.random_delay'):
            
            mock_fill.return_value = True
            
            await self.handler._fill_return_date(test_date)
            
            mock_fill.assert_called_once()
            args = mock_fill.call_args[0]
            assert args[1] == "return_date"
            assert args[2] == "2024-08-08"

    @pytest.mark.asyncio
    async def test_trigger_search_success(self):
        """Test successful search triggering."""
        with patch('flight_scraper.core.form_handler.robust_click') as mock_click, \
             patch('flight_scraper.core.form_handler.random_delay'), \
             patch.object(self.handler, '_wait_and_validate_search') as mock_validate:
            
            mock_click.return_value = True
            mock_validate.return_value = None
            
            await self.handler.trigger_search()
            
            mock_click.assert_called_once()
            args = mock_click.call_args[0]
            assert args[1] == "search_button"
            mock_validate.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_search_fallback(self):
        """Test search triggering with fallback methods."""
        with patch('flight_scraper.core.form_handler.robust_click') as mock_click, \
             patch('flight_scraper.core.form_handler.random_delay'), \
             patch.object(self.handler, '_fallback_search_strategies') as mock_fallback, \
             patch.object(self.handler, '_wait_and_validate_search') as mock_validate:
            
            mock_click.return_value = False
            mock_fallback.return_value = True
            mock_validate.return_value = None
            
            await self.handler.trigger_search()
            
            mock_fallback.assert_called_once()
            mock_validate.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_search_all_fail(self):
        """Test search triggering when all methods fail."""
        with patch('flight_scraper.core.form_handler.robust_click') as mock_click, \
             patch('flight_scraper.core.form_handler.random_delay'), \
             patch.object(self.handler, '_fallback_search_strategies') as mock_fallback:
            
            mock_click.return_value = False
            mock_fallback.return_value = False
            
            with pytest.raises(ScrapingError, match="Failed to trigger search with any method"):
                await self.handler.trigger_search()

    @pytest.mark.asyncio
    async def test_fallback_search_strategies_js_success(self):
        """Test fallback search strategies with JavaScript success."""
        with patch('flight_scraper.core.form_handler.random_delay'):
            self.mock_page.evaluate.return_value = None
            
            result = await self.handler._fallback_search_strategies()
            
            assert result is True
            self.mock_page.evaluate.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_search_strategies_enter_success(self):
        """Test fallback search strategies with Enter key success."""
        with patch('flight_scraper.core.form_handler.random_delay'):
            self.mock_page.evaluate.side_effect = Exception("JS failed")
            
            result = await self.handler._fallback_search_strategies()
            
            assert result is True
            self.mock_page.keyboard.press.assert_called_once_with('Enter')

    @pytest.mark.asyncio
    async def test_fallback_search_strategies_all_fail(self):
        """Test fallback search strategies when all fail."""
        with patch('flight_scraper.core.form_handler.random_delay'):
            self.mock_page.evaluate.side_effect = Exception("JS failed")
            self.mock_page.keyboard.press.side_effect = Exception("Enter failed")
            
            result = await self.handler._fallback_search_strategies()
            
            assert result is False

    @pytest.mark.asyncio
    async def test_wait_and_validate_search(self):
        """Test search validation."""
        self.mock_page.url = "https://www.google.com/travel/flights/search?param=value"
        
        with patch('flight_scraper.core.form_handler.random_delay'):
            await self.handler._wait_and_validate_search()
        
        # Should complete without raising exception

    @pytest.mark.asyncio
    async def test_wait_and_validate_search_no_search_param(self):
        """Test search validation when URL doesn't contain search params."""
        self.mock_page.url = "https://www.google.com/travel/flights"
        
        with patch('flight_scraper.core.form_handler.random_delay'):
            # Should complete without raising exception (just logs warning)
            await self.handler._wait_and_validate_search()