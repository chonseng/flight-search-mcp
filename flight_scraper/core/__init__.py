"""Core functionality for the Google Flights scraper.

This module contains the main scraper implementation, data models, 
configuration settings, and utility functions.
"""

from .scraper import GoogleFlightsScraper, scrape_flights_async
from .models import (
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
from .config import SCRAPER_CONFIG, GOOGLE_FLIGHTS_URLS, SELECTORS, LOG_CONFIG, OUTPUT_CONFIG

__all__ = [
    # Scraper functionality
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
    
    # Configuration
    "SCRAPER_CONFIG",
    "GOOGLE_FLIGHTS_URLS",
    "SELECTORS",
    "LOG_CONFIG",
    "OUTPUT_CONFIG"
]