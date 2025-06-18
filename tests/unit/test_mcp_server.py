"""Unit tests for MCP server functionality."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import date, datetime

from flight_scraper.mcp.server import search_flights_impl, get_scraper_status_impl, serialize_for_json, create_mcp_server
from flight_scraper.core.models import SearchCriteria, TripType, FlightOffer, FlightSegment, ScrapingResult


class TestMCPServer:
    """Test MCP server functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sample_result = ScrapingResult(
            search_criteria=SearchCriteria(
                origin="JFK",
                destination="LAX",
                departure_date=date(2024, 7, 15),
                trip_type=TripType.ONE_WAY,
                max_results=10
            ),
            flights=[
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
                            duration="5h 30m"
                        )
                    ]
                )
            ],
            total_results=1,
            success=True,
            execution_time=2.5
        )

    def test_serialize_for_json_datetime(self):
        """Test JSON serialization for datetime objects."""
        dt = datetime(2024, 7, 15, 10, 30, 45)
        result = serialize_for_json(dt)
        assert result == "2024-07-15T10:30:45"

    def test_serialize_for_json_model_dump(self):
        """Test JSON serialization for objects with model_dump method."""
        mock_obj = Mock()
        mock_obj.model_dump.return_value = {"key": "value"}
        
        result = serialize_for_json(mock_obj)
        assert result == {"key": "value"}

    def test_serialize_for_json_dict_method(self):
        """Test JSON serialization for objects with dict method."""
        mock_obj = Mock()
        mock_obj.dict.return_value = {"data": "test"}
        # Remove model_dump to test dict fallback
        del mock_obj.model_dump
        
        result = serialize_for_json(mock_obj)
        assert result == {"data": "test"}

    def test_serialize_for_json_string_fallback(self):
        """Test JSON serialization fallback to string."""
        class CustomObj:
            def __str__(self):
                return "custom_string"
        
        obj = CustomObj()
        result = serialize_for_json(obj)
        assert result == "custom_string"

    @pytest.mark.asyncio
    async def test_search_flights_success_one_way(self):
        """Test successful one-way flight search via MCP."""
        with patch('flight_scraper.mcp.server.scrape_flights_async') as mock_scrape:
            mock_scrape.return_value = self.sample_result
            
            result = await search_flights_impl(
                origin="JFK",
                destination="LAX",
                departure_date="2024-07-15",
                trip_type="one_way",
                max_results=10,
                headless=True
            )
            
            assert result["success"] is True
            assert result["total_results"] == 1
            assert len(result["flights"]) == 1
            assert result["flights"][0]["price"] == "$350"
            assert result["search_criteria"]["origin"] == "JFK"
            assert result["search_criteria"]["destination"] == "LAX"
            assert result["search_criteria"]["trip_type"] == "one_way"
            
            # Verify scrape_flights_async was called with correct parameters
            mock_scrape.assert_called_once()
            call_args = mock_scrape.call_args
            assert call_args.kwargs["origin"] == "JFK"
            assert call_args.kwargs["destination"] == "LAX"
            assert call_args.kwargs["departure_date"] == date(2024, 7, 15)
            assert call_args.kwargs["return_date"] is None
            assert call_args.kwargs["max_results"] == 10
            assert call_args.kwargs["headless"] is True

    @pytest.mark.asyncio
    async def test_search_flights_success_round_trip(self):
        """Test successful round-trip flight search via MCP."""
        round_trip_result = ScrapingResult(
            search_criteria=SearchCriteria(
                origin="NYC",
                destination="SF",
                departure_date=date(2024, 8, 1),
                return_date=date(2024, 8, 8),
                trip_type=TripType.ROUND_TRIP,
                max_results=5
            ),
            flights=[],
            total_results=0,
            success=True,
            execution_time=3.1
        )
        
        with patch('flight_scraper.mcp.server.scrape_flights_async') as mock_scrape:
            mock_scrape.return_value = round_trip_result
            
            result = await search_flights_impl(
                origin="NYC",
                destination="SF",
                departure_date="2024-08-01",
                return_date="2024-08-08",
                trip_type="round_trip",
                max_results=5,
                headless=False
            )
            
            assert result["success"] is True
            assert result["search_criteria"]["return_date"] == "2024-08-08"
            assert result["search_criteria"]["trip_type"] == "round_trip"
            
            # Verify parameters
            call_args = mock_scrape.call_args
            assert call_args.kwargs["return_date"] == date(2024, 8, 8)
            assert call_args.kwargs["headless"] is False

    @pytest.mark.asyncio
    async def test_search_flights_invalid_airport_codes(self):
        """Test flight search with invalid airport codes."""
        result = await search_flights_impl(
            origin="",
            destination="LAX",
            departure_date="2024-07-15"
        )
        
        assert result["success"] is False
        assert "Invalid airport codes" in result["error"]

    @pytest.mark.asyncio
    async def test_search_flights_invalid_date_format(self):
        """Test flight search with invalid date format."""
        result = await search_flights_impl(
            origin="JFK",
            destination="LAX",
            departure_date="invalid-date"
        )
        
        assert result["success"] is False
        assert "Invalid date format" in result["error"]

    @pytest.mark.asyncio
    async def test_search_flights_invalid_return_date(self):
        """Test flight search with invalid return date format."""
        result = await search_flights_impl(
            origin="JFK",
            destination="LAX",
            departure_date="2024-07-15",
            return_date="bad-date"
        )
        
        assert result["success"] is False
        assert "Invalid date format" in result["error"]

    @pytest.mark.asyncio
    async def test_search_flights_invalid_trip_type(self):
        """Test flight search with invalid trip type."""
        result = await search_flights_impl(
            origin="JFK",
            destination="LAX",
            departure_date="2024-07-15",
            trip_type="invalid_type"
        )
        
        assert result["success"] is False
        assert "Invalid trip_type" in result["error"]

    @pytest.mark.asyncio
    async def test_search_flights_max_results_limit(self):
        """Test flight search respects max results limit."""
        with patch('flight_scraper.mcp.server.scrape_flights_async') as mock_scrape:
            mock_scrape.return_value = self.sample_result
            
            await search_flights_impl(
                origin="JFK",
                destination="LAX",
                departure_date="2024-07-15",
                max_results=100  # Over limit
            )
            
            # Should be capped at 50
            call_args = mock_scrape.call_args
            assert call_args.kwargs["max_results"] == 50

    @pytest.mark.asyncio
    async def test_search_flights_scraping_failure(self):
        """Test flight search when scraping fails."""
        failed_result = ScrapingResult(
            search_criteria=SearchCriteria(
                origin="JFK",
                destination="LAX",
                departure_date=date(2024, 7, 15),
                trip_type=TripType.ONE_WAY,
                max_results=10
            ),
            flights=[],
            total_results=0,
            success=False,
            error_message="Scraping failed due to timeout",
            execution_time=30.0
        )
        
        with patch('flight_scraper.mcp.server.scrape_flights_async') as mock_scrape:
            mock_scrape.return_value = failed_result
            
            result = await search_flights_impl(
                origin="JFK",
                destination="LAX",
                departure_date="2024-07-15"
            )
            
            assert result["success"] is False
            assert result["error"] == "Scraping failed due to timeout"
            assert result["total_results"] == 0
            assert len(result["flights"]) == 0

    @pytest.mark.asyncio
    async def test_search_flights_exception(self):
        """Test flight search with unexpected exception."""
        with patch('flight_scraper.mcp.server.scrape_flights_async') as mock_scrape:
            mock_scrape.side_effect = Exception("Unexpected error")
            
            result = await search_flights_impl(
                origin="JFK",
                destination="LAX",
                departure_date="2024-07-15"
            )
            
            assert result["success"] is False
            assert "Flight search failed: Unexpected error" in result["error"]
            assert "execution_time" in result

    @pytest.mark.asyncio
    async def test_search_flights_default_parameters(self):
        """Test flight search with default parameters."""
        with patch('flight_scraper.mcp.server.scrape_flights_async') as mock_scrape:
            mock_scrape.return_value = self.sample_result
            
            result = await search_flights_impl(
                origin="DFW",
                destination="SEA",
                departure_date="2024-09-01"
                # All other parameters use defaults
            )
            
            assert result["success"] is True
            
            # Check defaults were applied
            call_args = mock_scrape.call_args
            assert call_args.kwargs["return_date"] is None
            assert call_args.kwargs["max_results"] == 10
            assert call_args.kwargs["headless"] is True

    @pytest.mark.asyncio
    async def test_get_scraper_status_success(self):
        """Test successful scraper status check."""
        with patch('flight_scraper.core.scraper.GoogleFlightsScraper') as MockScraper:
            mock_scraper_instance = AsyncMock()
            MockScraper.return_value.__aenter__.return_value = mock_scraper_instance
            MockScraper.return_value.__aexit__.return_value = None
            
            result = await get_scraper_status_impl()
            
            assert result["success"] is True
            assert result["scraper_status"]["browser_test"] is True
            assert result["scraper_status"]["browser_error"] is None
            assert "search_flights" in result["scraper_status"]["available_tools"]
            assert "get_scraper_status" in result["scraper_status"]["available_tools"]
            assert result["supported_features"]["trip_types"] == ["one_way", "round_trip"]
            assert result["supported_features"]["max_results_limit"] == 50
            assert result["supported_features"]["async_operation"] is True
            assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_get_scraper_status_browser_failure(self):
        """Test scraper status check with browser initialization failure."""
        with patch('flight_scraper.core.scraper.GoogleFlightsScraper') as MockScraper:
            MockScraper.return_value.__aenter__.side_effect = Exception("Browser init failed")
            MockScraper.return_value.__aexit__.return_value = None
            
            result = await get_scraper_status_impl()
            
            assert result["success"] is True
            assert result["scraper_status"]["browser_test"] is False
            assert "Browser init failed" in result["scraper_status"]["browser_error"]

    @pytest.mark.asyncio
    async def test_get_scraper_status_exception(self):
        """Test scraper status check with unexpected exception."""
        # Mock the logger to raise an exception early in the function
        with patch('flight_scraper.mcp.server.logger') as mock_logger:
            mock_logger.info.side_effect = Exception("Logger failed")
            
            result = await get_scraper_status_impl()
            
            assert result["success"] is False
            assert "Scraper status check failed: Logger failed" in result["error"]
            assert "timestamp" in result

    def test_create_mcp_server(self):
        """Test MCP server creation."""
        server = create_mcp_server()
        
        assert server is not None
        # FastMCP server should have the correct name
        assert hasattr(server, 'name')

    @pytest.mark.asyncio
    async def test_search_flights_flight_serialization(self):
        """Test proper serialization of flight data with timestamps."""
        # Create a result with timestamp data
        flight_with_timestamp = FlightOffer(
            price="$400",
            stops=1,
            total_duration="6h 15m",
            segments=[
                FlightSegment(
                    airline="United",
                    departure_airport="JFK",
                    arrival_airport="LAX",
                    departure_time="9:00 AM",
                    arrival_time="3:15 PM",
                    duration="6h 15m"
                )
            ]
        )
        
        result_with_timestamp = ScrapingResult(
            search_criteria=SearchCriteria(
                origin="JFK",
                destination="LAX",
                departure_date=date(2024, 7, 15),
                trip_type=TripType.ONE_WAY,
                max_results=10
            ),
            flights=[flight_with_timestamp],
            total_results=1,
            success=True,
            execution_time=2.8
        )
        
        with patch('flight_scraper.mcp.server.scrape_flights_async') as mock_scrape:
            mock_scrape.return_value = result_with_timestamp
            
            result = await search_flights_impl(
                origin="JFK",
                destination="LAX",
                departure_date="2024-07-15"
            )
            
            assert result["success"] is True
            assert len(result["flights"]) == 1
            flight_data = result["flights"][0]
            
            # Check that flight data is properly serialized
            assert "price" in flight_data
            assert "segments" in flight_data
            assert "scraped_at" in flight_data
            
            # Check search criteria serialization
            assert result["search_criteria"]["departure_date"] == "2024-07-15"
            assert "scraped_at" in result

    @pytest.mark.asyncio
    async def test_search_flights_execution_time_tracking(self):
        """Test that execution times are properly tracked."""
        with patch('flight_scraper.mcp.server.scrape_flights_async') as mock_scrape:
            mock_scrape.return_value = self.sample_result
            
            result = await search_flights_impl(
                origin="JFK",
                destination="LAX",
                departure_date="2024-07-15"
            )
            
            assert result["success"] is True
            assert result["execution_time"] == 2.5  # From sample_result
            assert "mcp_execution_time" in result  # Should have MCP execution time

    @pytest.mark.asyncio
    async def test_search_flights_airport_code_normalization(self):
        """Test that airport codes are properly normalized."""
        with patch('flight_scraper.mcp.server.scrape_flights_async') as mock_scrape:
            mock_scrape.return_value = self.sample_result
            
            await search_flights_impl(
                origin="  jfk  ",  # Should be normalized to "JFK"
                destination="lax",   # Should be normalized to "LAX"
                departure_date="2024-07-15"
            )
            
            call_args = mock_scrape.call_args
            assert call_args.kwargs["origin"] == "JFK"
            assert call_args.kwargs["destination"] == "LAX"