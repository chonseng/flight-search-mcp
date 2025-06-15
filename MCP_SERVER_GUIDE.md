# Google Flights MCP Server Guide

This document provides comprehensive information about the Google Flights MCP (Model Context Protocol) server implementation.

## Overview

The Google Flights MCP Server exposes the flight scraping functionality as MCP tools that can be used by AI assistants and other MCP clients. It provides a standardized interface for flight searches, airport information, and scraper status checks.

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright Browsers** (if not already installed):
   ```bash
   playwright install
   ```

## Starting the Server

### Basic Usage
```bash
python run_mcp_server.py
```
This starts the server on `localhost:8000`.

### Advanced Usage
```bash
# Custom port
python run_mcp_server.py --port 8080

# Allow external connections
python run_mcp_server.py --host 0.0.0.0

# Enable debug logging
python run_mcp_server.py --debug

# Custom log file
python run_mcp_server.py --log-file /path/to/custom.log

# Combination
python run_mcp_server.py --host 0.0.0.0 --port 9000 --debug
```

## Available MCP Tools

### 1. `search_flights`

Search for flights between airports with comprehensive options.

**Parameters:**
- `origin` (string, required): Origin airport code or city name (e.g., "JFK", "New York")
- `destination` (string, required): Destination airport code or city name (e.g., "LAX", "Los Angeles")
- `departure_date` (string, required): Departure date in YYYY-MM-DD format
- `return_date` (string, optional): Return date in YYYY-MM-DD format (for round-trip)
- `trip_type` (string, optional): "one_way" or "round_trip" (default: "one_way")
- `max_results` (integer, optional): Maximum results to return, 1-50 (default: 10)
- `headless` (boolean, optional): Run browser in headless mode (default: true)

**Example Response:**
```json
{
  "success": true,
  "search_criteria": {
    "origin": "JFK",
    "destination": "LAX",
    "departure_date": "2024-07-15",
    "return_date": null,
    "trip_type": "one_way",
    "max_results": 10
  },
  "flights": [
    {
      "price": "$269",
      "currency": "USD",
      "stops": 0,
      "total_duration": "6h 31m",
      "segments": [
        {
          "airline": "Delta",
          "departure_time": "8:00 AM",
          "arrival_time": "11:31 AM",
          "duration": "6h 31m"
        }
      ],
      "scraped_at": "2024-06-15T14:55:00"
    }
  ],
  "total_results": 5,
  "execution_time": 45.2
}
```

### 2. `get_airport_info`

Get airport code information and normalize airport queries.

**Parameters:**
- `query` (string, required): Airport code or city name to look up

**Example Response:**
```json
{
  "success": true,
  "original_query": "New York",
  "normalized_code": "JFK",
  "matched_city": "new york",
  "is_valid_code": true,
  "suggestions": []
}
```

### 3. `get_scraper_status`

Check the health and configuration of the flight scraper.

**Parameters:** None

**Example Response:**
```json
{
  "success": true,
  "scraper_status": {
    "browser_test": true,
    "browser_error": null,
    "available_tools": ["search_flights", "get_airport_info", "get_scraper_status"]
  },
  "configuration": {
    "timeout": 30000,
    "navigation_timeout": 60000,
    "retry_attempts": 3,
    "default_headless": true
  },
  "supported_features": {
    "trip_types": ["one_way", "round_trip"],
    "max_results_limit": 50,
    "async_operation": true
  }
}
```

## Supported Airport Codes

The server includes mappings for common cities to airport codes:

| City | Airport Code |
|------|--------------|
| New York, NYC | JFK |
| Los Angeles, LA | LAX |
| San Francisco, SF | SFO |
| Chicago | ORD |
| Miami | MIA |
| Boston | BOS |
| Seattle | SEA |
| Denver | DEN |
| Atlanta | ATL |
| Dallas | DFW |
| And many more... |

## Error Handling

The MCP server provides comprehensive error handling:

- **Invalid airport codes**: Returns suggestions for similar cities
- **Invalid dates**: Clear error messages about date format requirements
- **Scraping failures**: Detailed error information with troubleshooting hints
- **Browser issues**: Status checks and initialization errors
- **Network timeouts**: Automatic retry logic with exponential backoff

## Logging

The server uses structured logging with different levels:

- **INFO**: General operation information
- **DEBUG**: Detailed debugging information (use `--debug` flag)
- **ERROR**: Error conditions and failures
- **WARNING**: Non-critical issues

Log files are automatically rotated (10MB max) and retained for 7 days.

## Performance Considerations

- **Headless Mode**: Always use headless mode in production (`headless: true`)
- **Max Results**: Limit results to reasonable numbers (10-20 for interactive use)
- **Concurrent Requests**: The server handles one request at a time for browser stability
- **Caching**: Consider implementing caching for frequently requested routes

## Integration Examples

### Using with MCP Client Libraries

```python
# Example using mcp client
import asyncio
from mcp import ClientSession

async def search_flights_example():
    async with ClientSession("http://localhost:8000") as session:
        result = await session.call_tool("search_flights", {
            "origin": "JFK",
            "destination": "LAX", 
            "departure_date": "2024-07-15",
            "max_results": 5
        })
        print(f"Found {len(result['flights'])} flights")
```

### Direct HTTP API Usage

```bash
# Using curl to test the server
curl -X POST http://localhost:8000/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "name": "search_flights",
    "arguments": {
      "origin": "JFK",
      "destination": "LAX",
      "departure_date": "2024-07-15"
    }
  }'
```

## Troubleshooting

### Common Issues

1. **"Browser initialization failed"**
   - Install Playwright browsers: `playwright install`
   - Check system requirements for Playwright

2. **"Port already in use"**
   - Use a different port: `--port 8080`
   - Check for other running services

3. **"Import errors"**
   - Install requirements: `pip install -r requirements.txt`
   - Check Python version compatibility

4. **"No flights found"**
   - Verify airport codes are correct
   - Check date format (YYYY-MM-DD)
   - Try with different search parameters

### Debug Mode

Enable debug mode for detailed logging:
```bash
python run_mcp_server.py --debug
```

This provides:
- Detailed browser automation logs
- Network request/response information
- Element selection debugging
- Performance timing information

## Production Deployment

For production deployment:

1. **Use environment variables** for configuration
2. **Enable proper logging** with log rotation
3. **Set up monitoring** for server health
4. **Use process managers** like systemd or supervisor
5. **Configure firewall rules** appropriately
6. **Consider load balancing** for high traffic

Example systemd service file:
```ini
[Unit]
Description=Google Flights MCP Server
After=network.target

[Service]
Type=simple
User=mcpuser
WorkingDirectory=/path/to/flight-scrapper-2
ExecStart=/usr/bin/python run_mcp_server.py --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Security Considerations

- **Network Access**: Only expose to trusted networks
- **Rate Limiting**: Implement rate limiting for public deployments
- **Input Validation**: All inputs are validated, but monitor for abuse
- **Browser Security**: Playwright runs in sandbox mode
- **Logging**: Avoid logging sensitive information

## API Reference

Complete API documentation is available when the server is running at:
- Server info: `http://localhost:8000/`
- Health check: `http://localhost:8000/health`
- Tool definitions: `http://localhost:8000/tools`