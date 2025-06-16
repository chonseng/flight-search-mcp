# Google Flights Scraper

A simple, maintainable web scraper for Google Flights with MCP (Model Context Protocol) server support.

## Features

- **Flight Search**: Search for flights between airports with flexible date options
- **MCP Server**: Expose scraping capabilities via MCP protocol for AI assistants
- **Airport Normalization**: Automatic conversion of city names to airport codes
- **Robust Scraping**: Handles dynamic content and provides fallback strategies

## Quick Start

### Installation

```bash
pip install -r requirements.txt
playwright install
```

### Usage

#### MCP Server (for AI assistants)

```bash
# Start MCP server in stdio mode (recommended for AI assistants)
python mcp_server.py

# Or use the main entry point
python main.py mcp --stdio
```

#### CLI Usage

The CLI provides a powerful interface for searching flights with various options:

```bash
# Basic one-way flight search
python main.py cli scrape JFK LAX 2024-07-01

# Round-trip flight search
python main.py cli scrape JFK LAX 2024-07-01 --return 2024-07-10

# Search with maximum results limit
python main.py cli scrape JFK LAX 2024-07-01 --max-results 20

# Run in headless mode (no browser window)
python main.py cli scrape JFK LAX 2024-07-01 --headless

# Save results to JSON file
python main.py cli scrape JFK LAX 2024-07-01 --format json --output flights.json

# Save results to CSV file
python main.py cli scrape JFK LAX 2024-07-01 --format csv --output flights.csv

# Enable verbose logging for debugging
python main.py cli scrape JFK LAX 2024-07-01 --verbose

# Complex example: Round-trip search with all options
python main.py cli scrape "New York" "Los Angeles" 2024-07-01 \
  --return 2024-07-10 \
  --max-results 25 \
  --format json \
  --output my_flights.json \
  --headless \
  --verbose
```

**CLI Command Options:**
- `origin`: Origin airport code or city name (e.g., JFK, "New York")
- `destination`: Destination airport code or city name (e.g., LAX, "Los Angeles")
- `departure_date`: Departure date in YYYY-MM-DD format
- `--return, -r`: Return date for round-trip flights (YYYY-MM-DD)
- `--max-results, -m`: Maximum number of results (default: 50)
- `--format, -f`: Output format - table, json, or csv (default: table)
- `--output, -o`: Output file path for saving results
- `--headless`: Run browser in headless mode (no GUI)
- `--verbose, -v`: Enable verbose logging

**View CLI examples:**
```bash
python main.py cli example
```

#### Direct Python Usage

```python
from flight_scraper.core.scraper import scrape_flights_async
from datetime import date

# Search for flights
result = await scrape_flights_async(
    origin="JFK",
    destination="LAX", 
    departure_date=date(2024, 6, 15),
    max_results=10
)

print(f"Found {len(result.flights)} flights")
for flight in result.flights:
    print(f"{flight.price} - {flight.segments[0].airline}")
```

## Project Structure

```
flight_scraper/
├── core/
│   ├── scraper.py      # Main scraping logic
│   ├── models.py       # Data models
│   └── config.py       # Configuration
├── mcp/
│   └── server.py       # MCP server implementation
├── cli/
│   └── main.py         # CLI interface
└── utils.py            # Utility functions

mcp_server.py           # Standalone MCP server (stdio mode)
main.py                 # Main entry point
```

## MCP Tools

The MCP server provides three tools:

1. **search_flights**: Search for flights between airports
2. **get_airport_info**: Get airport code information and suggestions
3. **get_scraper_status**: Check if the scraper is working properly

## Configuration

The scraper automatically handles:
- Browser stealth settings to avoid detection
- Retry logic for failed requests
- Dynamic element detection
- Airport code normalization

## Debugging

Enable debug logging:

```bash
python main.py mcp --debug
```

## Requirements

- Python 3.8+
- Playwright (for browser automation)
- FastMCP (for MCP server)
- Loguru (for logging)
- Pydantic (for data validation)

## Notes

- The scraper is designed to be respectful of Google's servers
- Uses random delays to avoid being detected as a bot
- Handles various Google Flights page layouts
- Provides comprehensive error handling and logging