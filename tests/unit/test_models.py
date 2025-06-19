"""Unit tests for flight scraper models."""

import unittest
from datetime import date, timedelta

from flight_scraper.core.models import FlightOffer, FlightSegment, SearchCriteria, TripType


class TestModels(unittest.TestCase):
    """Test data models."""

    def test_search_criteria_creation(self):
        """Test SearchCriteria model creation."""
        criteria = SearchCriteria(
            origin="LAX", destination="NYC", departure_date=date.today(), max_results=10
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
            duration="5h 30m",
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
            duration="5h 30m",
        )

        offer = FlightOffer(price="$350", stops=0, total_duration="5h 30m", segments=[segment])

        self.assertEqual(offer.price, "$350")
        self.assertEqual(offer.stops, 0)
        self.assertEqual(len(offer.segments), 1)

    def test_trip_type_enum(self):
        """Test TripType enum values."""
        self.assertEqual(TripType.ONE_WAY, "one_way")
        self.assertEqual(TripType.ROUND_TRIP, "round_trip")

    def test_search_criteria_round_trip(self):
        """Test SearchCriteria with round trip."""
        departure_date = date.today() + timedelta(days=30)
        return_date = departure_date + timedelta(days=7)

        criteria = SearchCriteria(
            origin="LAX",
            destination="JFK",
            departure_date=departure_date,
            return_date=return_date,
            trip_type=TripType.ROUND_TRIP,
        )

        self.assertEqual(criteria.trip_type, TripType.ROUND_TRIP)
        self.assertEqual(criteria.return_date, return_date)


if __name__ == "__main__":
    unittest.main(verbosity=2)
