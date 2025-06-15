"""Configuration settings for the Google Flights scraper."""

import os
from typing import Dict, Any

# Scraper settings
SCRAPER_CONFIG = {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "viewport": {"width": 1366, "height": 768},
    "timeout": 30000,  # 30 seconds
    "navigation_timeout": 60000,  # 60 seconds
    "wait_for_results": 10000,  # 10 seconds to wait for flight results
    "retry_attempts": 3,
    "delay_range": (2, 5),  # Random delay between 2-5 seconds
}

# Google Flights URLs
GOOGLE_FLIGHTS_URLS = {
    "base": "https://www.google.com/travel/flights?tfs=CBwQARoAQAFIAXABggELCP___________wGYAQI&tfu=KgIIAw",
    "round_trip": "https://www.google.com/travel/flights?tfs=CBwQARoOagwIAhIIL20vMGQ5anIaDnIMCAISCC9tLzBkOWpyQAFIAXABggELCP___________wGYAQE&tfu=KgIIAg",
    "search": "https://www.google.com/travel/flights/search",
}

# Selectors for Google Flights elements
SELECTORS = {
    "from_input": 'input[placeholder*="Where from"]',
    "to_input": 'input[placeholder*="Where to"]',
    "departure_date": 'input[placeholder*="Departure"]',
    "return_date": 'input[placeholder*="Return"]',
    "search_button": 'button[aria-label*="Search"]',
    "flight_results": '[data-testid="flight-offer"]',
    "flight_cards": '.pIav2d',
    "airline_name": '.Ir0Voe',
    "departure_time": '.wtdjmc .eoY5cb:first-child',
    "arrival_time": '.wtdjmc .eoY5cb:last-child',
    "duration": '.gvkrdb',
    "stops": '.EfT7Ae .ogfYpf',
    "price": '.f8F1md .YMlIz',
    "airports": '.G2WY5c',
}

# Logging configuration
LOG_CONFIG = {
    "level": "INFO",
    "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    "file": "flight_scraper.log",
    "rotation": "10 MB",
    "retention": "7 days",
}

# Output settings
OUTPUT_CONFIG = {
    "default_format": "json",
    "csv_delimiter": ",",
    "max_results": 50,
}