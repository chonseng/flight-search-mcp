"""Core functionality for the Google Flights scraper.

This module contains the refactored scraper implementation with modular
component architecture, data models, configuration settings, and utility functions.

Components:
- BrowserManager: Browser lifecycle management with stealth settings
- FormHandler: Google Flights navigation and form interactions
- DataExtractor: Flight data extraction with multiple strategies
- GoogleFlightsScraper: Main orchestrator using component architecture
"""

from .browser_manager import BrowserManager
from .config import GOOGLE_FLIGHTS_URLS, LOG_CONFIG, OUTPUT_CONFIG, SCRAPER_CONFIG, SELECTORS
from .data_extractor import DataExtractor
from .form_handler import FormHandler
from .models import (
    ElementNotFoundError,
    FlightOffer,
    FlightSegment,
    NavigationError,
    ScrapingError,
    ScrapingResult,
    SearchCriteria,
    TimeoutError,
    TripType,
)
from .scraper import GoogleFlightsScraper, scrape_flights_async

__all__ = [
    # Main scraper functionality
    "GoogleFlightsScraper",
    "scrape_flights_async",
    # Refactored components
    "BrowserManager",
    "FormHandler",
    "DataExtractor",
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
    # Configuration
    "SCRAPER_CONFIG",
    "GOOGLE_FLIGHTS_URLS",
    "SELECTORS",
    "LOG_CONFIG",
    "OUTPUT_CONFIG",
]
