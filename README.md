# Google Flights Scraper

A comprehensive web scraper for Google Flights built with Python and Playwright. This tool automates the process of searching for flights and extracting detailed flight information including prices, airlines, schedules, and more.

## Features

- **Automated Flight Search**: Searches both one-way and round-trip flights
- **Web Automation**: Uses Playwright for reliable browser automation
- **Human-like Behavior**: Implements delays and stealth techniques to avoid detection
- **Multiple Output Formats**: Export results to JSON, CSV, or display in terminal
- **Comprehensive Data Extraction**: Captures airline, times, duration, stops, prices, and more
- **Error Handling**: Robust error handling with retry mechanisms
- **Logging**: Detailed logging for debugging and monitoring
- **CLI Interface**: Easy-to-use command-line interface

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   ```

## Usage

### Basic Commands

**One-way flight search:**
```bash
python main.py scrape LAX NYC 2025-07-01
```

**Round-trip flight search:**
```bash
python main.py scrape LAX NYC 2025-07-01 --return 2025-07-10
```

**Save results to JSON:**
```bash
python main.py scrape LAX NYC 2025-07-01 --format json --output flights.json
```

**Save results to CSV:**
```bash
python main.py scrape LAX NYC 2025-07-01 --format csv --output flights.csv
```

### Command Line Options

```bash
python main.py scrape [ORIGIN] [DESTINATION] [DEPARTURE_DATE] [OPTIONS]
```

**Required Arguments:**
- `ORIGIN`: Origin airport code (e.g., LAX, JFK, NYC)
- `DESTINATION`: Destination airport code (e.g., NYC, SFO, LAX)
- `DEPARTURE_DATE`: Departure date in YYYY-MM-DD format

**Optional Arguments:**
- `--return, -r`: Return date for round-trip flights (YYYY-MM-DD)
- `--max-results, -m`: Maximum number of results to return (default: 50)
- `--format, -f`: Output format - table, json, or csv (default: table)
- `--output, -o`: Output file path
- `--headless`: Run browser in headless mode (faster but no visual feedback)
- `--verbose, -v`: Enable verbose logging for debugging

### Examples

**View usage examples:**
```bash
python main.py example
```

**Advanced search with all options:**
```bash
python main.py scrape LAX NYC 2025-07-01 \
  --return 2025-07-10 \
  --max-results 25 \
  --format json \
  --output my_flights.json \
  --verbose
```

## Project Structure

```
flight-scrapper-2/
├── main.py              # CLI interface and main entry point
├── scraper.py           # Core scraping logic using Playwright
├── models.py            # Data models and type definitions
├── utils.py             # Utility functions and helpers
├── config.py            # Configuration settings and constants
├── requirements.txt     # Python dependencies
├── README.md           # This documentation
└── flight_scraper.log  # Log file (created automatically)
```

## How It Works

1. **Browser Initialization**: Launches a Chromium browser with stealth settings
2. **Navigation**: Goes to Google Flights homepage
3. **Form Filling**: Automatically fills in search criteria (origin, destination, dates)
4. **Search Execution**: Clicks search button and waits for results
5. **Data Extraction**: Scrapes flight information from result cards
6. **Data Processing**: Cleans and structures the extracted data
7. **Output**: Displays results or saves to file in specified format

## Data Extracted

For each flight, the scraper extracts:

- **Airline name**
- **Departure and arrival times**
- **Flight duration**
- **Number of stops**
- **Price**
- **Currency**
- **Flight segments** (for multi-leg flights)

## Configuration

The scraper can be customized by modifying [`config.py`](config.py):

- **Browser settings** (user agent, viewport size, timeouts)
- **Selector mappings** for different Google Flights page layouts
- **Delay settings** for human-like behavior
- **Logging configuration**

## Error Handling

The scraper includes comprehensive error handling for:

- **Network issues** (timeouts, connection errors)
- **Element detection** (missing buttons, form fields)
- **Data extraction** (malformed flight data)
- **Browser crashes** (automatic cleanup)

All errors are logged to [`flight_scraper.log`](flight_scraper.log) for debugging.

## Best Practices

1. **Use reasonable delays**: Don't set max-results too high to avoid being blocked
2. **Monitor logs**: Check the log file if scraping fails
3. **Respect robots.txt**: This tool is for educational/personal use
4. **Test with small batches**: Start with fewer results to test functionality
5. **Use headless mode**: For production use, enable headless mode for better performance

## Troubleshooting

**Common Issues:**

1. **"Element not found" errors**: Google Flights may have updated their page structure. Check [`config.py`](config.py) selectors.

2. **Timeout errors**: Increase timeout values in [`config.py`](config.py) or check internet connection.

3. **No results found**: Verify airport codes and dates are valid.

4. **Browser launch fails**: Ensure Playwright browsers are installed: `playwright install chromium`

**Enable verbose logging for debugging:**
```bash
python main.py scrape LAX NYC 2025-07-01 --verbose
```

## Technical Details

- **Language**: Python 3.8+
- **Web Automation**: Playwright (Chromium)
- **HTML Parsing**: BeautifulSoup4
- **CLI Framework**: Typer
- **Data Validation**: Pydantic
- **Logging**: Loguru
- **Output Formatting**: Rich (for terminal display)

## Limitations

- **Rate limiting**: Google may block requests if too many are made quickly
- **Page structure changes**: Google Flights updates may break selectors
- **Geographic restrictions**: Some flights may not be available in all regions
- **Dynamic pricing**: Prices may change between scraping runs

## Legal Notice

This tool is intended for educational and personal use only. Users are responsible for complying with Google's Terms of Service and applicable laws. The authors are not responsible for any misuse of this software.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this scraper.

## License

This project is open source and available under the MIT License.