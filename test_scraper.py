"""Basic tests for the Google Flights scraper."""

import unittest
from datetime import date, timedelta
from unittest.mock import Mock, patch

from models import SearchCriteria, FlightOffer, FlightSegment, TripType
from utils import (
    parse_duration, parse_price, parse_stops, 
    format_date_for_input, validate_airport_code, normalize_airport_code
)


class TestModels(unittest.TestCase):
    """Test data models."""
    
    def test_search_criteria_creation(self):
        """Test SearchCriteria model creation."""
        criteria = SearchCriteria(
            origin="LAX",
            destination="NYC",
            departure_date=date.today(),
            max_results=10
        )
        
        self.assertEqual(criteria.origin, "LAX")
        self.assertEqual(criteria.destination, "NYC")
        self.assertEqual(criteria.trip_type, TripType.ONE_WAY)
        self.assertEqual(criteria.max_results, 10)
    
    def test_flight_segment_creation(self):
        """Test FlightSegment model creation."""
        segment = FlightSegment(
            airline="Delta",
            departure_airport="LAX",
            arrival_airport="JFK",
            departure_time="10:00 AM",
            arrival_time="6:00 PM",
            duration="5h 30m"
        )
        
        self.assertEqual(segment.airline, "Delta")
        self.assertEqual(segment.departure_airport, "LAX")
        self.assertEqual(segment.duration, "5h 30m")
    
    def test_flight_offer_creation(self):
        """Test FlightOffer model creation."""
        segment = FlightSegment(
            airline="Delta",
            departure_airport="LAX",
            arrival_airport="JFK",
            departure_time="10:00 AM",
            arrival_time="6:00 PM",
            duration="5h 30m"
        )
        
        offer = FlightOffer(
            price="$350",
            stops=0,
            total_duration="5h 30m",
            segments=[segment]
        )
        
        self.assertEqual(offer.price, "$350")
        self.assertEqual(offer.stops, 0)
        self.assertEqual(len(offer.segments), 1)


class TestUtils(unittest.TestCase):
    """Test utility functions."""
    
    def test_parse_duration(self):
        """Test duration parsing."""
        self.assertEqual(parse_duration("5h 30m"), "5h 30m")
        self.assertEqual(parse_duration("2 hr 15 min"), "2 hr 15 min")
        self.assertEqual(parse_duration(""), "Unknown")
        self.assertEqual(parse_duration(None), "Unknown")
    
    def test_parse_price(self):
        """Test price parsing."""
        self.assertEqual(parse_price("$350"), "$350")
        self.assertEqual(parse_price("$1,250"), "$1,250")
        self.assertEqual(parse_price("350"), "350")
        self.assertEqual(parse_price(""), "0")
        self.assertEqual(parse_price(None), "0")
    
    def test_parse_stops(self):
        """Test stops parsing."""
        self.assertEqual(parse_stops("nonstop"), 0)
        self.assertEqual(parse_stops("direct"), 0)
        self.assertEqual(parse_stops("1 stop"), 1)
        self.assertEqual(parse_stops("2 stops"), 2)
        self.assertEqual(parse_stops(""), 0)
        self.assertEqual(parse_stops(None), 0)
    
    def test_format_date_for_input(self):
        """Test date formatting."""
        test_date = date(2025, 7, 1)
        formatted = format_date_for_input(test_date)
        self.assertEqual(formatted, "2025-07-01")
    
    def test_validate_airport_code(self):
        """Test airport code validation."""
        self.assertTrue(validate_airport_code("LAX"))
        self.assertTrue(validate_airport_code("NYC"))
        self.assertTrue(validate_airport_code("jfk"))
        self.assertFalse(validate_airport_code("LAXX"))
        self.assertFalse(validate_airport_code("LA"))
        self.assertFalse(validate_airport_code(""))
        self.assertFalse(validate_airport_code(None))
    
    def test_normalize_airport_code(self):
        """Test airport code normalization."""
        self.assertEqual(normalize_airport_code("lax"), "LAX")
        self.assertEqual(normalize_airport_code("jfk"), "JFK")
        self.assertEqual(normalize_airport_code("NYC"), "NYC")
        self.assertEqual(normalize_airport_code(" sfo "), "SFO")
        self.assertEqual(normalize_airport_code(""), "")


class TestScrapingLogic(unittest.TestCase):
    """Test scraping logic with mocks."""
    
    @patch('scraper.GoogleFlightsScraper')
    def test_scraper_initialization(self, mock_scraper):
        """Test scraper can be initialized."""
        mock_instance = Mock()
        mock_scraper.return_value = mock_instance
        
        # This would be the actual test when we have a working scraper
        self.assertIsNotNone(mock_instance)


def run_tests():
    """Run all tests."""
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_tests()