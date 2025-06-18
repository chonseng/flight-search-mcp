# MCP Server Guide

This guide provides comprehensive instructions for setting up, configuring, and using the Model Context Protocol (MCP) server for the Flight Search MCP.

> **📚 Documentation Navigation:**
> - **[README.md](README.md)** - Quick start and basic usage
> - **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development workflow and standards
> - **[DEVELOPMENT.md](DEVELOPMENT.md)** - Detailed architecture and debugging
> - **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Comprehensive testing instructions

## Table of Contents

- [Overview](#overview)
- [Quick Setup](#quick-setup)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

## Overview

The Flight Scraper MCP Server provides a standardized interface for flight data collection through the Model Context Protocol. It enables AI assistants and applications to search for flights programmatically with robust error handling and comprehensive data extraction.

### Key Features

- **Robust Flight Search**: Multi-strategy approach to handle Google Flights interface changes
- **Health Monitoring**: Real-time selector health monitoring and failure detection
- **Flexible Search Options**: Support for one-way and round-trip flights
- **Error Recovery**: Comprehensive fallback strategies for reliable data extraction
- **Performance Tracking**: Detailed execution metrics and success rates

### Architecture

The MCP server wraps the refactored flight scraper components:
- **BrowserManager**: Handles browser lifecycle with stealth settings
- **FormHandler**: Manages Google Flights navigation and form interactions
- **DataExtractor**: Extracts flight data using multiple extraction strategies

## Quick Setup

### Prerequisites
- Python 3.8+ and basic dependencies (see [README.md](README.md#requirements))
- Completed installation from [README.md](README.md#installation)

### MCP Server Startup

```bash
# Method 1: Direct execution
python mcp_server.py

# Method 2: Console script (after installation)
flight-scraper-mcp

# Method 3: Legacy entry point
python main.py mcp --stdio
```

### Verify MCP Server

```bash
# Test server creation
python -c "from flight_scraper.mcp.server import create_mcp_server; server = create_mcp_server(); print('✅ MCP server ready')"
```

> **💡 For detailed installation instructions, see [README.md](README.md#installation)**

## Configuration

### MCP Server Configuration

The MCP server can be configured through various methods:

#### 1. Direct Configuration
```python
from flight_scraper.mcp.server import create_mcp_server

# Create server with custom settings
server = create_mcp_server({
    "headless": True,
    "timeout": 30000,
    "max_results": 25,
    "enable_monitoring": True
})
```

#### 2. Environment Variables
```bash
export FLIGHT_SCRAPER_HEADLESS=true
export FLIGHT_SCRAPER_TIMEOUT=30000
export FLIGHT_SCRAPER_MAX_RESULTS=50
```

#### 3. Configuration File
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
  },
  "monitoring": {
    "enabled": true,
    "health_check_interval": 300
  }
}
```

### Browser Configuration

The scraper uses Chromium with anti-detection settings:
- Custom user agent to appear as regular browser
- Disabled automation flags
- Stealth JavaScript injection
- Configurable viewport and timeouts

## Usage Examples

### Basic Flight Search

```python
import asyncio
from datetime import date
from flight_scraper.core.scraper import scrape_flights_async

async def search_flights():
    """Basic flight search example."""
    result = await scrape_flights_async(
        origin="NYC",
        destination="LAX",
        departure_date=date(2024, 7, 15),
        return_date=date(2024, 7, 22),
        max_results=10,
        headless=True
    )
    
    if result.success:
        print(f"✅ Found {len(result.flights)} flights")
        for flight in result.flights:
            print(f"  💰 {flight.price} - {flight.segments[0].airline}")
            print(f"     🕐 {flight.segments[0].departure_time} → {flight.segments[0].arrival_time}")
            print(f"     ✈️  {flight.total_duration}, {flight.stops} stops")
    else:
        print(f"❌ Search failed: {result.error_message}")

# Run the search
asyncio.run(search_flights())
```

### Using the MCP Server Directly

```python
from flight_scraper.mcp.server import create_mcp_server
import asyncio

async def mcp_search_example():
    """Example using MCP server interface."""
    server = create_mcp_server()
    
    # Search for flights using MCP tool
    search_params = {
        "origin": "San Francisco",
        "destination": "New York",
        "departure_date": "2024-08-01",
        "return_date": "2024-08-08",
        "trip_type": "round_trip",
        "max_results": 15,
        "headless": True
    }
    
    result = await server.call_tool("search_flights", search_params)
    
    if result["success"]:
        print(f"MCP Search Results: {len(result['flights'])} flights found")
        for flight in result["flights"]:
            print(f"  {flight['price']} - {flight['airline']}")
    else:
        print(f"MCP Search failed: {result['error']}")

asyncio.run(mcp_search_example())
```

### Advanced Search with Health Monitoring

```python
from flight_scraper.core.scraper import GoogleFlightsScraper
from flight_scraper.core.models import SearchCriteria, TripType
import asyncio
from datetime import date

async def advanced_search_with_monitoring():
    """Advanced search with health monitoring."""
    
    criteria = SearchCriteria(
        origin="Chicago",
        destination="Miami",
        departure_date=date(2024, 9, 10),
        return_date=date(2024, 9, 17),
        trip_type=TripType.ROUND_TRIP,
        max_results=20
    )
    
    async with GoogleFlightsScraper(headless=False) as scraper:
        # Perform search
        result = await scraper.scrape_flights(criteria)
        
        # Get health report
        health_report = scraper.get_health_report()
        
        print(f"Search Results: {result.success}")
        print(f"Flights Found: {len(result.flights)}")
        print(f"Execution Time: {result.execution_time:.2f}s")
        
        # Health monitoring
        if health_report.get('overall_health'):
            success_rate = health_report['overall_health'].get('average_success_rate', 0)
            print(f"Selector Success Rate: {success_rate:.1%}")
        
        if health_report.get('critical_issues'):
            print("⚠️ Critical Issues Detected:")
            for issue in health_report['critical_issues']:
                print(f"  - {issue}")

asyncio.run(advanced_search_with_monitoring())
```

## API Reference

### MCP Server Tools

#### `search_flights`

Search for flights between airports with comprehensive parameters.

**Parameters:**
- `origin` (string, required): Origin airport code or city name
- `destination` (string, required): Destination airport code or city name  
- `departure_date` (string, required): Departure date in YYYY-MM-DD format
- `return_date` (string, optional): Return date for round-trip searches
- `trip_type` (string): "one_way" or "round_trip" (default: "one_way")
- `max_results` (integer): Maximum results to return (1-50, default: 10)
- `headless` (boolean): Run browser in headless mode (default: true)

**Response Format:**
```json
{
  "success": true,
  "flights": [
    {
      "price": "$299",
      "currency": "USD",
      "stops": 0,
      "total_duration": "5h 30m",
      "segments": [
        {
          "airline": "American Airlines",
          "flight_number": "AA123",
          "departure_airport": "JFK",
          "arrival_airport": "LAX",
          "departure_time": "8:00 AM",
          "arrival_time": "11:30 AM",
          "duration": "5h 30m"
        }
      ],
      "scraped_at": "2024-06-15T10:30:00Z"
    }
  ],
  "total_results": 15,
  "execution_time": 12.5,
  "search_criteria": {
    "origin": "JFK",
    "destination": "LAX",
    "departure_date": "2024-07-15",
    "trip_type": "one_way"
  }
}
```

#### `get_scraper_status`

Check the health and configuration of the scraper system.

**Parameters:** None

**Response Format:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "components": {
    "browser_manager": "initialized",
    "form_handler": "ready", 
    "data_extractor": "ready"
  },
  "health_metrics": {
    "average_success_rate": 0.95,
    "total_searches": 150,
    "recent_failures": 2
  },
  "configuration": {
    "headless_mode": true,
    "timeout": 30000,
    "max_results": 50
  }
}
```

### Core Classes

#### `GoogleFlightsScraper`

Main scraper class with component architecture.

**Methods:**
- `initialize()`: Initialize all components
- `scrape_flights(criteria)`: Perform flight search
- `cleanup()`: Clean up resources
- `get_health_report()`: Get health metrics

#### `SearchCriteria` 

Search parameters model.

**Attributes:**
- `origin`: Origin airport/city
- `destination`: Destination airport/city
- `departure_date`: Departure date
- `return_date`: Return date (optional)
- `trip_type`: ONE_WAY or ROUND_TRIP
- `max_results`: Maximum results

## Troubleshooting

### Common Issues and Solutions

#### 1. Browser Initialization Failures

**Symptom:** "Browser initialization failed" error
```
ScrapingError: Browser initialization failed: Playwright not found
```

**Solutions:**
- Reinstall Playwright: `pip uninstall playwright && pip install playwright`
- Install browsers: `playwright install chromium`
- Check system requirements: Ensure Chrome/Chromium dependencies are installed

#### 2. Selector Failures

**Symptom:** "Could not find element using any selector strategy"
```
ElementNotFoundError: Could not find 'From' input field using any selector strategy
```

**Solutions:**
- Check selector health: Use `get_health_report()` to identify failing selectors
- Update selector configurations in `utils.py`
- Verify Google Flights hasn't changed their interface
- Try running in non-headless mode for debugging

#### 3. Navigation Timeouts

**Symptom:** "Navigation failed" errors
```
NavigationError: Navigation failed with both primary and fallback URLs
```

**Solutions:**
- Increase timeout settings in configuration
- Check internet connection stability
- Verify Google Flights is accessible from your network
- Try different proxy settings if behind corporate firewall

#### 4. No Flight Results Found

**Symptom:** Successful scraping but zero flights returned
```
✅ Scraping completed successfully. Found 0 flights
```

**Solutions:**
- Verify search criteria (valid airports, realistic dates)
- Check if flights are available for the route
- Review extraction selectors - Google may have updated their interface
- Enable debug logging to see extraction details

#### 5. Memory/Performance Issues

**Symptom:** High memory usage or slow performance
```
Browser process consuming excessive memory
```

**Solutions:**
- Enable headless mode: `headless=True`
- Reduce max_results parameter
- Implement proper cleanup in async contexts
- Monitor browser processes and restart periodically

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
from loguru import logger

# Enable debug logging
logger.remove()
logger.add(lambda msg: print(msg, end=""), level="DEBUG", colorize=True)

# Run scraper with debug enabled
async with GoogleFlightsScraper(headless=False) as scraper:
    result = await scraper.scrape_flights(criteria)
```

### Health Monitoring

Use the built-in health monitoring to identify issues:

```python
# Get detailed health report
health_report = scraper.get_health_report()

# Check for critical issues
if health_report.get('critical_issues'):
    print("Critical Issues Found:")
    for issue in health_report['critical_issues']:
        print(f"  - {issue}")

# Review selector performance
overall_health = health_report.get('overall_health', {})
success_rate = overall_health.get('average_success_rate', 0)
if success_rate < 0.7:
    print(f"⚠️ Low success rate: {success_rate:.1%}")
    print("Consider updating selector configurations")
```

## Performance Optimization

## Advanced Topics

### Performance Optimization

For detailed performance optimization techniques, see [DEVELOPMENT.md](DEVELOPMENT.md#performance-optimization), including:
- Browser optimization settings
- Concurrent processing patterns
- Memory management strategies
- Caching implementations

### Security Considerations

The MCP server includes anti-detection measures and responsible usage patterns. For comprehensive security guidelines, see [DEVELOPMENT.md](DEVELOPMENT.md#security-and-best-practices), covering:
- Bot detection mitigation
- Rate limiting implementation
- Secure configuration management
- Responsible scraping practices

### Debugging and Troubleshooting

For advanced debugging techniques beyond basic troubleshooting, see [DEVELOPMENT.md](DEVELOPMENT.md#debugging-and-troubleshooting):
- Debug logging configuration
- Visual debugging with screenshots
- Selector diagnostics
- Memory and performance profiling

---

## Related Documentation

- **[README.md](README.md)** - Quick start, basic usage, and common troubleshooting
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development workflow, testing requirements, and code standards
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Detailed architecture, advanced configuration, and debugging
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Complete testing instructions and best practices

## Support

For MCP-specific issues:
1. **Check Health Reports**: Use [`get_scraper_status`](#get_scraper_status) tool
2. **Review Configuration**: Verify MCP server settings
3. **Test Core Functionality**: Ensure basic scraping works before MCP integration
4. **Monitor Performance**: Use built-in health monitoring for diagnostics

The MCP server is designed for reliability and maintainability with comprehensive monitoring and fallback strategies.