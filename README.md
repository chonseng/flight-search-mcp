# Flight Search MCP

Google Flights scraper with MCP server integration for AI assistants and automated flight data extraction.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Test Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen.svg)](tests/)

## 🚀 Quick Start

### Installation

```bash
# Install the package
pip install -e .

# Install Playwright browsers
playwright install chromium

# Verify installation
python verify_installation.py
```

### Basic Usage

```python
from flight_scraper.core import GoogleFlightsScraper, SearchCriteria
from datetime import date
import asyncio

async def search_flights():
    criteria = SearchCriteria(
        origin="JFK",
        destination="LAX", 
        departure_date=date(2024, 7, 15),
        max_results=10
    )
    
    async with GoogleFlightsScraper(headless=True) as scraper:
        result = await scraper.scrape_flights(criteria)
        
        if result.success:
            print(f"✅ Found {len(result.flights)} flights")
            for flight in result.flights[:3]:
                print(f"💰 {flight.price} - {flight.segments[0].airline}")
        else:
            print(f"❌ Search failed: {result.error_message}")

asyncio.run(search_flights())
```

### MCP Server

```bash
# Start MCP server in stdio mode (recommended for AI assistants)
python main.py mcp --stdio

# Alternative: Direct server with stdio mode
python -m flight_scraper.mcp.server --stdio

# Start server with HTTP interface (for development/testing)
python main.py mcp --host localhost --port 8000

# Alternative module syntax for HTTP mode
python -m flight_scraper.mcp.server --host localhost --port 8000
```

### CLI Usage

```bash
# Basic search
python main.py cli scrape JFK LAX 2024-07-01

# Round-trip with options
python main.py cli scrape JFK LAX 2024-07-01 \
  --return 2024-07-10 \
  --max-results 20 \
  --format json \
  --output flights.json

# Alternative module syntax
python -m flight_scraper.cli.main scrape JFK LAX 2024-07-01

# Additional options
python main.py cli scrape JFK LAX 2024-07-01 \
  --headless \
  --verbose \
  --max-results 50

# View CLI examples
python main.py cli example
```

## 🎯 Key Features

- **🔍 Robust Flight Search**: Multi-strategy scraping with fallback mechanisms
- **🤖 MCP Server Integration**: Expose capabilities via Model Context Protocol
- **🏗️ Modular Architecture**: Component-based design with [`BrowserManager`](flight_scraper/core/browser_manager.py:1), [`FormHandler`](flight_scraper/core/form_handler.py:1), [`DataExtractor`](flight_scraper/core/data_extractor.py:1)
- **⚡ Performance Monitoring**: Real-time health monitoring and diagnostics
- **🛡️ Anti-Detection**: Stealth browser settings and human-like patterns
- **📊 Multiple Formats**: JSON, CSV, and table output support

## ⚙️ Configuration

### Environment Variables

```bash
export FLIGHT_SCRAPER_HEADLESS=true
export FLIGHT_SCRAPER_TIMEOUT=30000
export FLIGHT_SCRAPER_MAX_RESULTS=50
export FLIGHT_SCRAPER_LOG_LEVEL=INFO
```

### Python Configuration

```python
from flight_scraper.core.config import get_config

# Get configuration
config = get_config()
print(f"Timeout: {config.scraper.timeout}")
print(f"Max Results: {config.scraper.max_results}")

# Custom configuration
custom_config = get_config(
    environment="production",
    scraper_timeout=60000,
    max_results=100
)
```

### Configuration File

Create `config.json`:
```json
{
  "scraper": {
    "headless": true,
    "timeout": 30000,
    "max_results": 50
  },
  "logging": {
    "level": "INFO",
    "file": "flight_scraper.log"
  }
}
```

## 🔧 Requirements

- **Python**: 3.8 or higher
- **Browser**: Chrome/Chromium (automatically installed by Playwright)
- **Memory**: Minimum 2GB RAM (4GB recommended)
- **Network**: Stable internet connection

## 🛠️ Troubleshooting

### Common Issues

#### Browser initialization failed
```bash
# Reinstall Playwright
pip uninstall playwright && pip install playwright
playwright install chromium
```

#### No results found
```python
# Enable debug mode
async with GoogleFlightsScraper(headless=False) as scraper:
    result = await scraper.scrape_flights(criteria)
    health = scraper.get_health_report()
    print(f"Health: {health}")
```

#### Timeout errors
```python
from flight_scraper.core.config import get_config

# Increase timeout
config = get_config(scraper_timeout=60000)  # 60 seconds
```

### Health Monitoring

```python
async with GoogleFlightsScraper() as scraper:
    result = await scraper.scrape_flights(criteria)
    
    # Check health
    health = scraper.get_health_report()
    if health.get('critical_issues'):
        print("Issues found:")
        for issue in health['critical_issues']:
            print(f"  - {issue}")
```

### Debug Mode

```python
import os
from loguru import logger

# Enable debug logging
os.environ['FLIGHT_SCRAPER_LOG_LEVEL'] = 'DEBUG'
logger.remove()
logger.add(lambda msg: print(msg, end=""), level="DEBUG")

# Run with debugging
async with GoogleFlightsScraper(headless=False) as scraper:
    result = await scraper.scrape_flights(criteria)
```

## 🧪 Testing

```bash
# Run unit tests (fast)
python -m unittest discover tests/unit -v

# Run integration tests
python tests/integration/test_scraper_integration.py

# Run with pytest and coverage
pytest tests/unit/ --cov=flight_scraper --cov-report=html
```

## 📚 Documentation

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development workflow, code standards, and contribution guidelines
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Detailed architecture, debugging, and advanced configuration  
- **[MCP Server Guide](MCP_SERVER_GUIDE.md)** - Complete MCP server setup and usage
- **[Testing Guide](TESTING_GUIDE.md)** - Comprehensive testing instructions

## 🤝 Getting Help

1. **Check Health Reports**: Use [`get_health_report()`](flight_scraper/core/scraper.py:1) for diagnostics
2. **Review Documentation**: See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed troubleshooting
3. **Run Diagnostics**: Use [`test_selector_diagnostics.py`](tests/diagnostics/test_selector_diagnostics.py:1)
4. **Enable Debug Logging**: Set `FLIGHT_SCRAPER_LOG_LEVEL=DEBUG`

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup and workflow
- Code quality standards and testing requirements
- Pull request process and guidelines

---

**Built with ❤️ for reliable flight data extraction**