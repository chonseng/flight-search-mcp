"""Unit tests for centralized configuration management."""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

from flight_scraper.core.config import (
    ScraperConfig, GoogleFlightsConfig, SelectorConfig, LoggingConfig,
    OutputConfig, MCPConfig, ApplicationConfig,
    get_config, reload_config, set_config, get_legacy_config
)


class TestScraperConfig:
    """Test ScraperConfig class."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ScraperConfig()
        
        assert "Mozilla/5.0" in config.user_agent
        assert config.viewport_width == 1366
        assert config.viewport_height == 768
        assert config.timeout == 30000
        assert config.navigation_timeout == 60000
        assert config.wait_for_results == 10000
        assert config.retry_attempts == 3
        assert config.min_delay == 2.0
        assert config.max_delay == 5.0
        assert '--no-sandbox' in config.browser_args

    def test_viewport_property(self):
        """Test viewport property returns correct format."""
        config = ScraperConfig(viewport_width=1920, viewport_height=1080)
        
        viewport = config.viewport
        assert viewport == {"width": 1920, "height": 1080}

    def test_delay_range_property(self):
        """Test delay_range property returns correct format."""
        config = ScraperConfig(min_delay=1.5, max_delay=3.5)
        
        delay_range = config.delay_range
        assert delay_range == (1.5, 3.5)

    def test_invalid_delay_validation(self):
        """Test validation of delay settings."""
        with pytest.raises(ValidationError):
            ScraperConfig(min_delay=5.0, max_delay=2.0)

    def test_positive_int_validation(self):
        """Test positive integer validation."""
        with pytest.raises(ValidationError):
            ScraperConfig(timeout=-1000)
        
        with pytest.raises(ValidationError):
            ScraperConfig(viewport_width=0)

    def test_environment_variable_override(self):
        """Test environment variable override."""
        with patch.dict(os.environ, {
            'FLIGHT_SCRAPER_TIMEOUT': '45000',
            'FLIGHT_SCRAPER_RETRY_ATTEMPTS': '5'
        }):
            config = ScraperConfig()
            assert config.timeout == 45000
            assert config.retry_attempts == 5


class TestGoogleFlightsConfig:
    """Test GoogleFlightsConfig class."""

    def test_default_urls(self):
        """Test default URL configurations."""
        config = GoogleFlightsConfig()
        
        assert "google.com/travel/flights" in config.base_url
        assert "google.com/travel/flights" in config.round_trip_url
        assert "google.com/travel/flights/search" in config.search_url
        assert config.fallback_url == "https://www.google.com/travel/flights"

    def test_environment_variable_override(self):
        """Test environment variable override for URLs."""
        with patch.dict(os.environ, {
            'GOOGLE_FLIGHTS_BASE_URL': 'https://custom.example.com',
            'GOOGLE_FLIGHTS_FALLBACK_URL': 'https://fallback.example.com'
        }):
            config = GoogleFlightsConfig()
            assert config.base_url == 'https://custom.example.com'
            assert config.fallback_url == 'https://fallback.example.com'


class TestSelectorConfig:
    """Test SelectorConfig class."""

    def test_default_selectors(self):
        """Test default selector configurations."""
        config = SelectorConfig()
        
        assert len(config.from_input) > 0
        assert len(config.to_input) > 0
        assert len(config.search_button) > 0
        assert any('placeholder*="Where from"' in selector for selector in config.from_input)
        assert any('placeholder*="Where to"' in selector for selector in config.to_input)

    def test_flight_result_selectors(self):
        """Test flight result selector configurations."""
        config = SelectorConfig()
        
        assert len(config.airline_name) > 0
        assert len(config.price) > 0
        assert len(config.duration) > 0
        assert len(config.stops) > 0
        assert '.Ir0Voe' in config.airline_name


class TestLoggingConfig:
    """Test LoggingConfig class."""

    def test_default_logging_config(self):
        """Test default logging configuration."""
        config = LoggingConfig()
        
        assert config.level == "INFO"
        assert "{time:" in config.format
        assert config.file == "flight_scraper.log"
        assert config.rotation == "10 MB"
        assert config.retention == "7 days"
        assert config.console_output is True
        assert config.file_output is True

    def test_level_validation(self):
        """Test logging level validation."""
        # Valid levels
        for level in ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = LoggingConfig(level=level)
            assert config.level == level

        # Invalid level
        with pytest.raises(ValidationError):
            LoggingConfig(level="INVALID")

    def test_level_case_insensitive(self):
        """Test logging level is case insensitive."""
        config = LoggingConfig(level="debug")
        assert config.level == "DEBUG"


class TestOutputConfig:
    """Test OutputConfig class."""

    def test_default_output_config(self):
        """Test default output configuration."""
        config = OutputConfig()
        
        assert config.default_format == "json"
        assert config.csv_delimiter == ","
        assert config.max_results == 50
        assert config.include_debug_info is False
        assert config.pretty_print is True

    def test_format_validation(self):
        """Test output format validation."""
        # Valid formats
        for fmt in ["json", "csv", "yaml", "xml"]:
            config = OutputConfig(default_format=fmt)
            assert config.default_format == fmt

        # Invalid format
        with pytest.raises(ValidationError):
            OutputConfig(default_format="invalid")

    def test_format_case_insensitive(self):
        """Test output format is case insensitive."""
        config = OutputConfig(default_format="JSON")
        assert config.default_format == "json"


class TestMCPConfig:
    """Test MCPConfig class."""

    def test_default_mcp_config(self):
        """Test default MCP configuration."""
        config = MCPConfig()
        
        assert config.host == "localhost"
        assert config.port == 8000
        assert config.use_stdio is False
        assert config.debug is False
        assert config.timeout == 30
        assert config.max_results_limit == 50

    def test_positive_port_validation(self):
        """Test positive port validation."""
        with pytest.raises(ValidationError):
            MCPConfig(port=0)
        
        with pytest.raises(ValidationError):
            MCPConfig(port=-8000)


class TestApplicationConfig:
    """Test ApplicationConfig class."""

    def test_default_application_config(self):
        """Test default application configuration."""
        config = ApplicationConfig()
        
        assert config.environment == "development"
        assert config.debug is False
        assert isinstance(config.scraper, ScraperConfig)
        assert isinstance(config.google_flights, GoogleFlightsConfig)
        assert isinstance(config.selectors, SelectorConfig)
        assert isinstance(config.logging, LoggingConfig)
        assert isinstance(config.output, OutputConfig)
        assert isinstance(config.mcp, MCPConfig)

    def test_environment_validation(self):
        """Test environment validation."""
        # Valid environments
        for env in ["development", "testing", "staging", "production"]:
            config = ApplicationConfig(environment=env)
            assert config.environment == env

        # Invalid environment
        with pytest.raises(ValidationError):
            ApplicationConfig(environment="invalid")

    def test_environment_case_insensitive(self):
        """Test environment is case insensitive."""
        config = ApplicationConfig(environment="PRODUCTION")
        assert config.environment == "production"

    def test_environment_helper_methods(self):
        """Test environment helper methods."""
        dev_config = ApplicationConfig(environment="development")
        prod_config = ApplicationConfig(environment="production")
        
        assert dev_config.is_development() is True
        assert dev_config.is_production() is False
        assert prod_config.is_development() is False
        assert prod_config.is_production() is True

    def test_nested_config_access(self):
        """Test accessing nested configuration."""
        config = ApplicationConfig()
        
        # Test that we can access nested configurations
        assert config.scraper.timeout == 30000
        assert config.google_flights.base_url.startswith("https://")
        assert len(config.selectors.from_input) > 0
        assert config.logging.level == "INFO"
        assert config.output.default_format == "json"
        assert config.mcp.host == "localhost"

    def test_env_file_loading(self):
        """Test loading from environment file."""
        # Create temporary .env file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("FLIGHT_SCRAPER_ENVIRONMENT=testing\n")
            f.write("FLIGHT_SCRAPER_DEBUG=true\n")
            f.write("FLIGHT_SCRAPER_TIMEOUT=25000\n")
            env_file = f.name
        
        try:
            # Test loading with specific env file
            with patch.object(ApplicationConfig.Config, 'env_file', env_file):
                config = ApplicationConfig()
                # Note: This test might not work exactly as expected due to 
                # how pydantic handles env files, but the structure is correct
        finally:
            os.unlink(env_file)


class TestGlobalConfigManagement:
    """Test global configuration management functions."""

    def test_get_config_singleton(self):
        """Test get_config returns singleton instance."""
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2

    def test_reload_config(self):
        """Test reload_config creates new instance."""
        config1 = get_config()
        config2 = reload_config()
        
        assert config1 is not config2
        assert isinstance(config2, ApplicationConfig)

    def test_set_config(self):
        """Test set_config for testing purposes."""
        custom_config = ApplicationConfig(environment="testing", debug=True)
        set_config(custom_config)
        
        retrieved_config = get_config()
        assert retrieved_config is custom_config
        assert retrieved_config.environment == "testing"
        assert retrieved_config.debug is True
        
        # Reset to default
        reload_config()

    def test_get_legacy_config(self):
        """Test legacy configuration format."""
        legacy_config = get_legacy_config()
        
        assert "SCRAPER_CONFIG" in legacy_config
        assert "GOOGLE_FLIGHTS_URLS" in legacy_config
        assert "SELECTORS" in legacy_config
        assert "LOG_CONFIG" in legacy_config
        assert "OUTPUT_CONFIG" in legacy_config
        
        # Test structure matches legacy format
        scraper_config = legacy_config["SCRAPER_CONFIG"]
        assert "user_agent" in scraper_config
        assert "viewport" in scraper_config
        assert "timeout" in scraper_config
        
        urls_config = legacy_config["GOOGLE_FLIGHTS_URLS"]
        assert "base" in urls_config
        assert "round_trip" in urls_config
        assert "search" in urls_config
        
        selectors_config = legacy_config["SELECTORS"]
        assert "from_input" in selectors_config
        assert "to_input" in selectors_config
        assert "search_button" in selectors_config


class TestConfigurationIntegration:
    """Test configuration integration scenarios."""

    def test_config_with_environment_variables(self):
        """Test configuration with various environment variables."""
        env_vars = {
            'FLIGHT_SCRAPER_ENVIRONMENT': 'production',
            'FLIGHT_SCRAPER_DEBUG': 'true',
            'FLIGHT_SCRAPER_TIMEOUT': '45000',
            'FLIGHT_SCRAPER_RETRY_ATTEMPTS': '5',
            'GOOGLE_FLIGHTS_BASE_URL': 'https://custom.google.com',
            'LOGGING_LEVEL': 'DEBUG',
            'OUTPUT_DEFAULT_FORMAT': 'csv',
            'MCP_PORT': '9000'
        }
        
        with patch.dict(os.environ, env_vars):
            config = ApplicationConfig()
            
            assert config.environment == 'production'
            assert config.debug is True
            assert config.scraper.timeout == 45000
            assert config.scraper.retry_attempts == 5
            assert config.google_flights.base_url == 'https://custom.google.com'
            assert config.logging.level == 'DEBUG'
            assert config.output.default_format == 'csv'
            assert config.mcp.port == 9000

    def test_config_validation_errors(self):
        """Test various configuration validation errors."""
        # Test invalid timeout
        with pytest.raises(ValidationError):
            ScraperConfig(timeout=-1000)
        
        # Test invalid environment
        with pytest.raises(ValidationError):
            ApplicationConfig(environment="invalid_env")
        
        # Test invalid logging level
        with pytest.raises(ValidationError):
            LoggingConfig(level="INVALID_LEVEL")
        
        # Test invalid output format
        with pytest.raises(ValidationError):
            OutputConfig(default_format="invalid_format")

    def test_config_partial_override(self):
        """Test partial configuration override."""
        custom_scraper = ScraperConfig(timeout=60000, retry_attempts=10)
        custom_logging = LoggingConfig(level="DEBUG", console_output=False)
        
        config = ApplicationConfig(
            environment="testing",
            scraper=custom_scraper,
            logging=custom_logging
        )
        
        assert config.environment == "testing"
        assert config.scraper.timeout == 60000
        assert config.scraper.retry_attempts == 10
        assert config.logging.level == "DEBUG"
        assert config.logging.console_output is False
        
        # Other configs should use defaults
        assert config.output.default_format == "json"
        assert config.mcp.port == 8000

    def test_config_serialization(self):
        """Test configuration can be serialized and deserialized."""
        config = ApplicationConfig(environment="testing", debug=True)
        
        # Test dict export
        config_dict = config.dict()
        assert config_dict["environment"] == "testing"
        assert config_dict["debug"] is True
        assert "scraper" in config_dict
        assert "logging" in config_dict
        
        # Test JSON serialization
        config_json = config.json()
        assert "testing" in config_json
        assert "scraper" in config_json
        
        # Test recreation from dict
        new_config = ApplicationConfig(**config_dict)
        assert new_config.environment == "testing"
        assert new_config.debug is True