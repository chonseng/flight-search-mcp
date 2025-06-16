"""Integration test script to verify the restructured package works correctly."""

import sys
from datetime import date, timedelta

def test_imports():
    """Test that all imports work correctly."""
    print("🧪 Testing package imports...")
    
    try:
        # Test main package import
        import flight_scraper
        print("✅ Main package imported")
        
        # Test core classes
        from flight_scraper import GoogleFlightsScraper, SearchCriteria, FlightOffer
        print("✅ Core classes imported")
        
        # Test async function
        from flight_scraper import scrape_flights_async
        print("✅ Async function imported")
        
        # Test CLI import
        from flight_scraper.cli.main import app
        print("✅ CLI app imported")
        
        # Test models
        from flight_scraper.core.models import TripType, ScrapingResult
        print("✅ Model classes imported")
        
        # Test config
        from flight_scraper.core.config import SCRAPER_CONFIG, GOOGLE_FLIGHTS_URLS
        print("✅ Configuration imported")
        
        # Test utils
        from flight_scraper.utils import normalize_airport_code, parse_price
        print("✅ Utility functions imported")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_functionality():
    """Test basic functionality without actually scraping."""
    print("\n🧪 Testing basic functionality...")
    
    try:
        from flight_scraper import SearchCriteria, TripType
        from flight_scraper.utils import normalize_airport_code, format_date_for_input
        
        # Test SearchCriteria creation
        criteria = SearchCriteria(
            origin=normalize_airport_code("jfk"),
            destination=normalize_airport_code("lax"),
            departure_date=date.today() + timedelta(days=30),
            trip_type=TripType.ONE_WAY,
            max_results=10
        )
        print(f"✅ SearchCriteria created: {criteria.origin} -> {criteria.destination}")
        
        # Test date formatting
        formatted_date = format_date_for_input(criteria.departure_date)
        print(f"✅ Date formatting works: {formatted_date}")
        
        # Test airport code normalization
        normalized = normalize_airport_code("Los Angeles")
        print(f"✅ Airport code normalization: 'Los Angeles' -> '{normalized}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test error: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Testing restructured flight scraper package...\n")
    
    import_success = test_imports()
    functionality_success = test_functionality()
    
    print(f"\n📊 Test Results:")
    print(f"   Imports: {'✅ PASS' if import_success else '❌ FAIL'}")
    print(f"   Functionality: {'✅ PASS' if functionality_success else '❌ FAIL'}")
    
    if import_success and functionality_success:
        print(f"\n🎉 All tests passed! Package restructuring successful.")
        print(f"\n📁 New package structure:")
        print(f"   flight_scraper/")
        print(f"   ├── __init__.py          # Main package exports")
        print(f"   ├── utils.py             # Utility functions")
        print(f"   ├── core/                # Core functionality")
        print(f"   │   ├── __init__.py      # Core package exports")
        print(f"   │   ├── scraper.py       # Main scraper class")
        print(f"   │   ├── models.py        # Pydantic models")
        print(f"   │   └── config.py        # Configuration settings")
        print(f"   ├── cli/                 # Command line interface")
        print(f"   │   ├── __init__.py      # CLI package exports")
        print(f"   │   └── main.py          # CLI implementation")
        print(f"   └── mcp/                 # MCP server (placeholder)")
        print(f"       ├── __init__.py      # MCP package exports")
        print(f"       └── server.py        # MCP server (future)")
        
        return 0
    else:
        print(f"\n❌ Some tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())