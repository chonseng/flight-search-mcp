"""Unit tests for flight scraper utilities."""

import unittest
from datetime import date

from flight_scraper.utils import (
    parse_duration, parse_price, parse_stops,
    format_date_for_input
)


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
    

    def test_parse_duration_edge_cases(self):
        """Test duration parsing edge cases."""
        self.assertEqual(parse_duration("0h 0m"), "0h 0m")
        self.assertEqual(parse_duration("24h 59m"), "24h 59m")
        self.assertEqual(parse_duration("1h"), "1h")
        self.assertEqual(parse_duration("30m"), "30m")
    
    def test_parse_price_edge_cases(self):
        """Test price parsing edge cases."""
        self.assertEqual(parse_price("$0"), "$0")
        self.assertEqual(parse_price("$10,000"), "$10,000")
        self.assertEqual(parse_price("USD 500"), "500")  # Only extracts the numeric part
        self.assertEqual(parse_price("€250"), "€250")
    
    def test_parse_stops_edge_cases(self):
        """Test stops parsing edge cases."""
        self.assertEqual(parse_stops("Non-stop"), 1)  # Returns 1 because it finds the number
        self.assertEqual(parse_stops("NONSTOP"), 0)   # Returns 0 because "nonstop" is in lower()
        self.assertEqual(parse_stops("3 stops"), 3)
        self.assertEqual(parse_stops("multiple stops"), 1)  # Default case when no number found
    


if __name__ == "__main__":
    unittest.main(verbosity=2)