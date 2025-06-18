"""Verify that the Google Flights scraper is properly installed and configured."""

import sys
import importlib
from datetime import date


def check_imports():
    """Check if all required modules can be imported."""
    required_modules = [
        ('playwright', 'Playwright'),
        ('typer', 'Typer'),
        ('loguru', 'Loguru'),
        ('pydantic', 'Pydantic'),
        ('rich', 'Rich'),
        ('bs4', 'BeautifulSoup4'),
        ('lxml', 'lxml'),
        ('dateutil', 'python-dateutil')
    ]
    
    print("🔍 Checking required modules...")
    all_good = True
    
    for module_name, display_name in required_modules:
        try:
            importlib.import_module(module_name)
            print(f"✅ {display_name}")
        except ImportError:
            print(f"❌ {display_name} - Not installed")
            all_good = False
    
    return all_good


def check_project_files():
    """Check if all project files exist."""
    required_files = [
        'main.py',
        'flight_scraper/core/scraper.py',
        'flight_scraper/core/models.py',
        'flight_scraper/utils.py',
        'flight_scraper/core/config.py',
        'requirements.txt',
        'README.md'
    ]
    
    print("\n📁 Checking project files...")
    all_good = True
    
    for filename in required_files:
        try:
            with open(filename, 'r') as f:
                content = f.read()
                if content.strip():
                    print(f"✅ {filename}")
                else:
                    print(f"⚠️  {filename} - File is empty")
                    all_good = False
        except FileNotFoundError:
            print(f"❌ {filename} - File not found")
            all_good = False
    
    return all_good


def check_local_imports():
    """Check if local modules can be imported."""
    local_modules = [
        'flight_scraper.core.config',
        'flight_scraper.core.models',
        'flight_scraper.utils',
        'flight_scraper.core.scraper'
    ]
    
    print("\n🐍 Checking local modules...")
    all_good = True
    
    for module_name in local_modules:
        try:
            importlib.import_module(module_name)
            print(f"✅ {module_name}")
        except ImportError as e:
            print(f"❌ {module_name} - Import error: {e}")
            all_good = False
    
    return all_good


def test_basic_functionality():
    """Test basic functionality of the scraper components."""
    print("\n⚙️  Testing basic functionality...")
    
    try:
        from flight_scraper.core.models import SearchCriteria, TripType
        from flight_scraper.utils import format_date_for_input
        
        # Test model creation
        criteria = SearchCriteria(
            origin="LAX",
            destination="NYC",
            departure_date=date.today(),
            trip_type=TripType.ONE_WAY
        )
        print("✅ SearchCriteria model creation")
        
        # Test utility functions
        formatted_date = format_date_for_input(date.today())
        assert len(formatted_date) == 10  # YYYY-MM-DD format
        print("✅ Date formatting")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False


def main():
    """Run all verification checks."""
    print("🛫 Google Flights Scraper - Installation Verification")
    print("=" * 60)
    
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print()
    
    # Run all checks
    checks = [
        ("Module Dependencies", check_imports),
        ("Project Files", check_project_files), 
        ("Local Imports", check_local_imports),
        ("Basic Functionality", test_basic_functionality)
    ]
    
    results = []
    for check_name, check_func in checks:
        result = check_func()
        results.append((check_name, result))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for check_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{check_name:.<30} {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All checks passed! The scraper is ready to use.")
        print("\nNext steps:")
        print("  1. Run 'python main.py cli example' to see usage examples")
        print("  2. Try 'python main.py cli scrape LAX NYC 2025-07-01' for a basic search")
        print("  3. Run 'python mcp_server.py' to test MCP server")
        print("  4. Check 'README.md' for detailed documentation")
    else:
        print("❌ Some checks failed. Please fix the issues above before using the scraper.")
        print("\nTroubleshooting:")
        print("  1. Run 'python install.py' to reinstall dependencies")
        print("  2. Make sure all files are in the correct directory")
        print("  3. Check that Python 3.8+ is installed")
        
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)