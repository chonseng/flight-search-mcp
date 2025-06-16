"""Pytest configuration and shared fixtures for flight scraper tests."""

import pytest
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture
def sample_search_criteria():
    """Sample search criteria for testing."""
    from flight_scraper.core.models import SearchCriteria, TripType
    from datetime import date, timedelta
    
    return SearchCriteria(
        origin="LAX",
        destination="JFK",
        departure_date=date.today() + timedelta(days=30),
        trip_type=TripType.ONE_WAY,
        max_results=10
    )

@pytest.fixture
def sample_flight_segment():
    """Sample flight segment for testing."""
    from flight_scraper.core.models import FlightSegment
    
    return FlightSegment(
        airline="Delta",
        departure_airport="LAX",
        arrival_airport="JFK",
        departure_time="10:00 AM",
        arrival_time="6:00 PM",
        duration="5h 30m"
    )

@pytest.fixture
def sample_flight_offer():
    """Sample flight offer for testing."""
    from flight_scraper.core.models import FlightOffer, FlightSegment
    
    segment = FlightSegment(
        airline="Delta",
        departure_airport="LAX",
        arrival_airport="JFK",
        departure_time="10:00 AM",
        arrival_time="6:00 PM",
        duration="5h 30m"
    )
    
    return FlightOffer(
        price="$350",
        stops=0,
        total_duration="5h 30m",
        segments=[segment]
    )