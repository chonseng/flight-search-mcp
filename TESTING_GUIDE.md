# Flight Scraper Testing Guide

This document provides comprehensive instructions for running tests in the flight scraper project.

## 📁 Test Directory Structure

```
tests/
├── __init__.py
├── conftest.py                    # pytest configuration with shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_models.py            # Tests for data models (5 tests)
│   ├── test_utils.py             # Tests for utility functions (11 tests)  
│   └── test_selectors.py         # Tests for robust selector logic (12 tests)
├── integration/
│   ├── __init__.py
│   ├── test_scraper_integration.py  # Package structure verification tests
│   └── test_robust_selectors.py     # Full system integration tests
└── diagnostics/
    ├── __init__.py
    └── test_selector_diagnostics.py # Selector debugging and health tests
```

## 🧪 How to Run Tests

### Prerequisites

Make sure you're in the project root directory:
```bash
cd /path/to/flight-scrapper-2
```

### 1. Run All Unit Tests

Run all 28 unit tests across all categories:
```bash
python -m unittest discover tests/unit -v
```

Expected output:
```
test_flight_offer_creation (test_models.TestModels.test_flight_offer_creation) ... ok
test_flight_segment_creation (test_models.TestModels.test_flight_segment_creation) ... ok
...
----------------------------------------------------------------------
Ran 28 tests in 0.009s

OK
```

### 2. Run Individual Test Categories

#### Model Tests (5 tests)
Test data models like SearchCriteria, FlightOffer, FlightSegment:
```bash
python -m unittest tests.unit.test_models -v
```

#### Utility Tests (11 tests)
Test utility functions like parse_price, parse_duration, normalize_airport_code:
```bash
python -m unittest tests.unit.test_utils -v
```

#### Selector Tests (12 tests)
Test robust selector logic and health monitoring:
```bash
python -m unittest tests.unit.test_selectors -v
```

### 3. Run Integration Tests

#### Package Integration Test
Verifies all imports work correctly:
```bash
python tests/integration/test_scraper_integration.py
```

Expected output:
```
🚀 Testing restructured flight scraper package...

🧪 Testing package imports...
✅ Main package imported
✅ Core classes imported
...
🎉 All tests passed! Package restructuring successful.
```

#### Robust Selector System Test
Full end-to-end test of the robust selector system:
```bash
python tests/integration/test_robust_selectors.py
```

**Note**: This test opens a browser and performs actual web scraping. Use with caution.

### 4. Run Diagnostic Tests

#### Selector Diagnostics
Specialized test for debugging selector issues:
```bash
python tests/diagnostics/test_selector_diagnostics.py
```

**Note**: This test also opens a browser and is intended for debugging selector problems.

### 5. Run Tests with pytest (Optional)

If you have pytest installed, you can use it for enhanced test reporting:

#### Install pytest (if not already installed)
```bash
pip install pytest
```

#### Run all tests with pytest
```bash
pytest tests/ -v
```

#### Run specific test categories with pytest
```bash
pytest tests/unit/ -v                    # All unit tests
pytest tests/unit/test_models.py -v      # Just model tests
pytest tests/integration/ -v             # All integration tests
pytest tests/diagnostics/ -v             # All diagnostic tests
```

#### Run tests with coverage (if pytest-cov is installed)
```bash
pip install pytest-cov
pytest tests/ --cov=flight_scraper --cov-report=html
```

## 📊 Test Categories Explained

### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual components in isolation
- **Fast execution**: Should run quickly (< 1 second)
- **No external dependencies**: Don't require browsers, network, or files
- **Categories**:
  - **Models**: Test Pydantic data models and enums
  - **Utils**: Test utility functions for parsing and validation
  - **Selectors**: Test robust selector classes and interfaces

### Integration Tests (`tests/integration/`)
- **Purpose**: Test how components work together
- **Moderate execution time**: May take several seconds
- **May require external resources**: Some tests open browsers
- **Categories**:
  - **Package Integration**: Verify all imports and package structure
  - **Robust Selectors**: End-to-end testing of the scraping system

### Diagnostic Tests (`tests/diagnostics/`)
- **Purpose**: Help debug issues and verify system health
- **Variable execution time**: Depends on what's being diagnosed
- **Interactive**: May open browsers and show visual feedback
- **Use cases**:
  - Debugging selector failures
  - Verifying system configuration
  - Testing specific scraping scenarios

## ⚡ Quick Test Commands

```bash
# Fast: Run only unit tests (28 tests, ~0.01s)
python -m unittest discover tests/unit -v

# Medium: Add integration tests (includes browser tests)
python tests/integration/test_scraper_integration.py

# Comprehensive: Run everything (may take several minutes)
python -m unittest discover tests/unit -v && \
python tests/integration/test_scraper_integration.py && \
python tests/integration/test_robust_selectors.py

# Debugging: Run diagnostic tests when something is wrong
python tests/diagnostics/test_selector_diagnostics.py
```

## 🔧 Troubleshooting

### Import Errors
If you get `ModuleNotFoundError: No module named 'flight_scraper'`:
```bash
# Make sure you're in the project root directory
pwd  # Should show .../flight-scrapper-2

# Make sure the flight_scraper package exists
ls flight_scraper/  # Should show __init__.py and other files
```

### Browser Tests Failing
Integration and diagnostic tests may fail if:
- No browser is available (install Chrome/Chromium)
- Network connectivity issues
- Google Flights site changes

### pytest Not Found
If `pytest` command fails:
```bash
# Install pytest
pip install pytest

# Or run with python module syntax
python -m pytest tests/ -v
```

## 📈 Test Status

- **Total Unit Tests**: 28 ✅
- **Models Tests**: 5 ✅
- **Utils Tests**: 11 ✅  
- **Selectors Tests**: 12 ✅
- **Integration Tests**: Working ✅
- **Import Verification**: Passing ✅

All tests are currently passing and the test structure follows Python testing best practices.