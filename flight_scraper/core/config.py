"""Centralized configuration management for the Google Flights scraper."""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field, validator
from pydantic.types import PositiveInt, PositiveFloat


class ScraperConfig(BaseSettings):
    """Core scraper configuration settings."""
    
    # Browser settings
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        description="User agent string for browser requests"
    )
    viewport_width: PositiveInt = Field(default=1366, description="Browser viewport width")
    viewport_height: PositiveInt = Field(default=768, description="Browser viewport height")
    
    # Timeout settings (in milliseconds)
    timeout: PositiveInt = Field(default=30000, description="Default page timeout in ms")
    navigation_timeout: PositiveInt = Field(default=60000, description="Navigation timeout in ms")
    wait_for_results: PositiveInt = Field(default=10000, description="Wait time for flight results in ms")
    
    # Retry and delay settings
    retry_attempts: PositiveInt = Field(default=3, description="Number of retry attempts")
    min_delay: PositiveFloat = Field(default=2.0, description="Minimum delay between actions in seconds")
    max_delay: PositiveFloat = Field(default=5.0, description="Maximum delay between actions in seconds")
    
    # Browser launch arguments
    browser_args: List[str] = Field(
        default=[
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor'
        ],
        description="Browser launch arguments for stealth mode"
    )
    
    @validator('min_delay', 'max_delay')
    def validate_delays(cls, v, values):
        """Validate delay settings."""
        if 'min_delay' in values and v < values['min_delay']:
            raise ValueError('max_delay must be greater than or equal to min_delay')
        return v
    
    @property
    def viewport(self) -> Dict[str, int]:
        """Get viewport configuration as dictionary."""
        return {"width": self.viewport_width, "height": self.viewport_height}
    
    @property
    def delay_range(self) -> tuple:
        """Get delay range as tuple."""
        return (self.min_delay, self.max_delay)

    class Config:
        env_prefix = "FLIGHT_SCRAPER_"
        case_sensitive = False


class GoogleFlightsConfig(BaseSettings):
    """Google Flights specific configuration."""
    
    # URLs
    base_url: str = Field(
        default="https://www.google.com/travel/flights?tfs=CBwQARoAQAFIAXABggELCP___________wGYAQI&tfu=KgIIAw",
        description="Base Google Flights URL"
    )
    round_trip_url: str = Field(
        default="https://www.google.com/travel/flights?tfs=CBwQARoOagwIAhIIL20vMGQ5anIaDnIMCAISCC9tLzBkOWpyQAFIAXABggELCP___________wGYAQE&tfu=KgIIAg",
        description="Round trip Google Flights URL"
    )
    search_url: str = Field(
        default="https://www.google.com/travel/flights/search",
        description="Google Flights search URL"
    )
    fallback_url: str = Field(
        default="https://www.google.com/travel/flights",
        description="Fallback URL when primary navigation fails"
    )

    class Config:
        env_prefix = "GOOGLE_FLIGHTS_"
        case_sensitive = False


class SelectorConfig(BaseSettings):
    """CSS selector configuration for Google Flights elements."""
    
    # Form input selectors
    from_input: List[str] = Field(
        default=[
            'input[placeholder*="Where from"]',
            'input[aria-label*="Where from"]',
            'input[data-testid*="origin"]',
            '.II2One .TP4Lpb input'
        ],
        description="Selectors for origin input field"
    )
    
    to_input: List[str] = Field(
        default=[
            'input[placeholder*="Where to"]',
            'input[aria-label*="Where to"]',
            'input[data-testid*="destination"]',
            '.II2One .TP4Lpb:last-child input'
        ],
        description="Selectors for destination input field"
    )
    
    departure_date: List[str] = Field(
        default=[
            'input[placeholder*="Departure"]',
            'input[aria-label*="Departure"]',
            'input[data-testid*="departure"]',
            '.II2One .eoY5cb input'
        ],
        description="Selectors for departure date field"
    )
    
    return_date: List[str] = Field(
        default=[
            'input[placeholder*="Return"]',
            'input[aria-label*="Return"]',
            'input[data-testid*="return"]',
            '.II2One .eoY5cb:last-child input'
        ],
        description="Selectors for return date field"
    )
    
    search_button: List[str] = Field(
        default=[
            'button[aria-label*="Search"]',
            'button[data-testid*="search"]',
            '.VfPpkd-LgbsSe[jsname="LgbsSe"]',
            '.RNNXgb'
        ],
        description="Selectors for search button"
    )
    
    # Flight result selectors
    flight_containers: List[str] = Field(
        default=[
            'div[role="tabpanel"] ul',
            '[data-testid="flight-offer"]',
            '.pIav2d',
            '.Rk10dc'
        ],
        description="Selectors for flight result containers"
    )
    
    airline_name: List[str] = Field(
        default=[
            '.Ir0Voe',
            '.sSHqwe',
            '[data-testid*="airline"]',
            'img[alt*="logo"]'
        ],
        description="Selectors for airline name"
    )
    
    departure_time: List[str] = Field(
        default=[
            '.wtdjmc .eoY5cb:first-child',
            '.zxVSec:first-child',
            '[data-testid*="departure-time"]'
        ],
        description="Selectors for departure time"
    )
    
    arrival_time: List[str] = Field(
        default=[
            '.wtdjmc .eoY5cb:last-child',
            '.zxVSec:last-child',
            '[data-testid*="arrival-time"]'
        ],
        description="Selectors for arrival time"
    )
    
    duration: List[str] = Field(
        default=[
            '.gvkrdb',
            '.AdWm1c',
            '[data-testid*="duration"]'
        ],
        description="Selectors for flight duration"
    )
    
    stops: List[str] = Field(
        default=[
            '.EfT7Ae .ogfYpf',
            '.c8rWCd',
            '[data-testid*="stops"]'
        ],
        description="Selectors for number of stops"
    )
    
    price: List[str] = Field(
        default=[
            '.f8F1md .YMlIz',
            '.U3gSDe',
            '[data-testid*="price"]',
            '[aria-label*="dollar"]'
        ],
        description="Selectors for flight price"
    )

    class Config:
        env_prefix = "SELECTORS_"
        case_sensitive = False


class LoggingConfig(BaseSettings):
    """Logging configuration settings."""
    
    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        description="Log message format"
    )
    file: Optional[str] = Field(default="flight_scraper.log", description="Log file path")
    rotation: str = Field(default="10 MB", description="Log file rotation size")
    retention: str = Field(default="7 days", description="Log file retention period")
    console_output: bool = Field(default=True, description="Enable console output")
    file_output: bool = Field(default=True, description="Enable file output")

    @validator('level')
    def validate_level(cls, v):
        """Validate logging level."""
        valid_levels = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid logging level. Must be one of: {valid_levels}")
        return v.upper()

    class Config:
        env_prefix = "LOGGING_"
        case_sensitive = False


class OutputConfig(BaseSettings):
    """Output configuration settings."""
    
    default_format: str = Field(default="json", description="Default output format")
    csv_delimiter: str = Field(default=",", description="CSV delimiter character")
    max_results: PositiveInt = Field(default=50, description="Maximum number of results")
    include_debug_info: bool = Field(default=False, description="Include debug information in output")
    pretty_print: bool = Field(default=True, description="Pretty print JSON output")

    @validator('default_format')
    def validate_format(cls, v):
        """Validate output format."""
        valid_formats = ["json", "csv", "yaml", "xml"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Invalid output format. Must be one of: {valid_formats}")
        return v.lower()

    class Config:
        env_prefix = "OUTPUT_"
        case_sensitive = False


class MCPConfig(BaseSettings):
    """MCP server configuration settings."""
    
    host: str = Field(default="localhost", description="MCP server host")
    port: PositiveInt = Field(default=8000, description="MCP server port")
    use_stdio: bool = Field(default=False, description="Use stdio mode instead of HTTP")
    debug: bool = Field(default=False, description="Enable debug logging for MCP server")
    timeout: PositiveInt = Field(default=30, description="Request timeout in seconds")
    max_results_limit: PositiveInt = Field(default=50, description="Maximum results limit for MCP requests")

    class Config:
        env_prefix = "MCP_"
        case_sensitive = False


class ApplicationConfig(BaseSettings):
    """Main application configuration that combines all settings."""
    
    # Environment settings
    environment: str = Field(default="development", description="Application environment")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Component configurations
    scraper: ScraperConfig = Field(default_factory=ScraperConfig)
    google_flights: GoogleFlightsConfig = Field(default_factory=GoogleFlightsConfig)
    selectors: SelectorConfig = Field(default_factory=SelectorConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)

    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment setting."""
        valid_envs = ["development", "testing", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Invalid environment. Must be one of: {valid_envs}")
        return v.lower()

    class Config:
        env_prefix = "FLIGHT_SCRAPER_"
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


# Global configuration instance
_config_instance: Optional[ApplicationConfig] = None


def get_config() -> ApplicationConfig:
    """
    Get the global configuration instance.
    
    Returns:
        ApplicationConfig: The global configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ApplicationConfig()
    return _config_instance


def reload_config() -> ApplicationConfig:
    """
    Reload the global configuration instance.
    
    Returns:
        ApplicationConfig: The reloaded configuration instance
    """
    global _config_instance
    _config_instance = ApplicationConfig()
    return _config_instance


def set_config(config: ApplicationConfig) -> None:
    """
    Set the global configuration instance (mainly for testing).
    
    Args:
        config: The configuration instance to set
    """
    global _config_instance
    _config_instance = config


# Legacy compatibility - maintain backward compatibility with existing code
def get_legacy_config() -> Dict[str, Any]:
    """
    Get configuration in legacy format for backward compatibility.
    
    Returns:
        Dict containing legacy configuration format
    """
    config = get_config()
    
    return {
        "SCRAPER_CONFIG": {
            "user_agent": config.scraper.user_agent,
            "viewport": config.scraper.viewport,
            "timeout": config.scraper.timeout,
            "navigation_timeout": config.scraper.navigation_timeout,
            "wait_for_results": config.scraper.wait_for_results,
            "retry_attempts": config.scraper.retry_attempts,
            "delay_range": config.scraper.delay_range,
        },
        "GOOGLE_FLIGHTS_URLS": {
            "base": config.google_flights.base_url,
            "round_trip": config.google_flights.round_trip_url,
            "search": config.google_flights.search_url,
        },
        "SELECTORS": {
            "from_input": config.selectors.from_input[0],  # Use first selector for compatibility
            "to_input": config.selectors.to_input[0],
            "departure_date": config.selectors.departure_date[0],
            "return_date": config.selectors.return_date[0],
            "search_button": config.selectors.search_button[0],
            "flight_results": config.selectors.flight_containers[0],
            "airline_name": config.selectors.airline_name[0],
            "departure_time": config.selectors.departure_time[0],
            "arrival_time": config.selectors.arrival_time[0],
            "duration": config.selectors.duration[0],
            "stops": config.selectors.stops[0],
            "price": config.selectors.price[0],
        },
        "LOG_CONFIG": {
            "level": config.logging.level,
            "format": config.logging.format,
            "file": config.logging.file,
            "rotation": config.logging.rotation,
            "retention": config.logging.retention,
        },
        "OUTPUT_CONFIG": {
            "default_format": config.output.default_format,
            "csv_delimiter": config.output.csv_delimiter,
            "max_results": config.output.max_results,
        }
    }


# Export legacy configuration for backward compatibility
legacy_config = get_legacy_config()
SCRAPER_CONFIG = legacy_config["SCRAPER_CONFIG"]
GOOGLE_FLIGHTS_URLS = legacy_config["GOOGLE_FLIGHTS_URLS"]
SELECTORS = legacy_config["SELECTORS"]
LOG_CONFIG = legacy_config["LOG_CONFIG"]
OUTPUT_CONFIG = legacy_config["OUTPUT_CONFIG"]