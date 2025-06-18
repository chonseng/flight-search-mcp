"""Google Flights Scraper Package.

A comprehensive web scraper for extracting flight information from Google Flights.
Features both CLI interface and MCP server for AI assistant integration.
"""

from .core.scraper import GoogleFlightsScraper, scrape_flights_async
from .core.models import (
    SearchCriteria,
    FlightOffer,
    FlightSegment,
    ScrapingResult,
    TripType,
    ScrapingError,
    NavigationError,
    ElementNotFoundError,
    TimeoutError
)

# MCP server functionality (optional import)
try:
    from .mcp.server import create_mcp_server
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False
    create_mcp_server = None

__version__ = "1.0.0"
__author__ = "Flight Scraper Team"
__description__ = "Google Flights web scraper with MCP server support"
__url__ = "https://github.com/yourusername/flight-scrapper-2"
__license__ = "MIT"

# Build information
__build_date__ = "2025-06-15"
__python_requires__ = ">=3.8"

__all__ = [
    # Main scraper classes and functions
    "GoogleFlightsScraper",
    "scrape_flights_async",
    
    # Data models
    "SearchCriteria",
    "FlightOffer",
    "FlightSegment",
    "ScrapingResult",
    "TripType",
    
    # Exceptions
    "ScrapingError",
    "NavigationError",
    "ElementNotFoundError",
    "TimeoutError",
    
    # MCP server functions (if available)
    "create_mcp_server",
    
    # Package metadata
    "__version__",
    "__author__",
    "__description__",
    "__url__",
    "__license__",
    "__build_date__",
    "__python_requires__"
]

# Conditional exports based on availability
if not _MCP_AVAILABLE:
    __all__.remove("create_mcp_server")


def get_package_info():
    """Get comprehensive package information."""
    return {
        "name": "google-flights-scraper",
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "url": __url__,
        "license": __license__,
        "build_date": __build_date__,
        "python_requires": __python_requires__,
        "mcp_available": _MCP_AVAILABLE,
        "components": {
            "core_scraper": True,
            "cli_interface": True,
            "mcp_server": _MCP_AVAILABLE
        }
    }


def check_dependencies():
    """Check if all required dependencies are available."""
    missing = []
    
    try:
        import playwright
    except ImportError:
        missing.append("playwright")
    
    try:
        import pydantic
    except ImportError:
        missing.append("pydantic")
    
    try:
        import typer
    except ImportError:
        missing.append("typer")
    
    if not _MCP_AVAILABLE:
        try:
            import fastmcp
        except ImportError:
            missing.append("fastmcp (for MCP server)")
    
    return {
        "all_satisfied": len(missing) == 0,
        "missing": missing,
        "mcp_available": _MCP_AVAILABLE
    }