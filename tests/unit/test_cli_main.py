"""Comprehensive unit tests for CLI main module."""

import pytest
import asyncio
import json
import csv
from unittest.mock import patch, Mock, AsyncMock, mock_open
from datetime import date, datetime
from pathlib import Path
from typer.testing import CliRunner
from io import StringIO

from flight_scraper.cli.main import (
    app, display_results, save_to_json, save_to_csv, scrape, example
)
from flight_scraper.core.models import (
    ScrapingResult, SearchCriteria, FlightOffer, FlightSegment, TripType
)


class TestDisplayResults:
    """Test display_results function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.search_criteria = SearchCriteria(
            origin="LAX",
            destination="NYC",
            departure_date=date(2025, 7, 1),
            trip_type=TripType.ONE_WAY,
            max_results=50
        )
        
        self.segment = FlightSegment(
            airline="American Airlines",
            flight_number="AA123",
            departure_airport="LAX",
            arrival_airport="JFK",
            departure_time="09:00",
            arrival_time="17:30",
            duration="5h 30m",
            aircraft="Boeing 737"
        )
        
        self.flight = FlightOffer(
            price="$299",
            currency="USD",
            stops=0,
            total_duration="5h 30m",
            segments=[self.segment]
        )

    @patch('flight_scraper.cli.main.console')
    def test_display_results_success(self, mock_console):
        """Test successful display of results."""
        result = ScrapingResult(
            search_criteria=self.search_criteria,
            flights=[self.flight],
            total_results=1,
            success=True,
            execution_time=2.5
        )
        
        display_results(result)
        
        # Should call console.print twice - once for table, once for summary
        assert mock_console.print.call_count == 2

    @patch('flight_scraper.cli.main.console')
    def test_display_results_failure(self, mock_console):
        """Test display of failed results."""
        result = ScrapingResult(
            search_criteria=self.search_criteria,
            flights=[],
            total_results=0,
            success=False,
            error_message="Network error",
            execution_time=1.0
        )
        
        display_results(result)
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "Scraping failed" in call_args
        assert "Network error" in call_args

    @patch('flight_scraper.cli.main.console')
    def test_display_results_no_flights(self, mock_console):
        """Test display when no flights found."""
        result = ScrapingResult(
            search_criteria=self.search_criteria,
            flights=[],
            total_results=0,
            success=True,
            execution_time=1.5
        )
        
        display_results(result)
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "No flights found" in call_args

    @patch('flight_scraper.cli.main.console')
    def test_display_results_no_segments(self, mock_console):
        """Test display with flight that has no segments."""
        flight_no_segments = FlightOffer(
            price="$299",
            currency="USD",
            stops=0,
            total_duration="5h 30m",
            segments=[]
        )
        
        result = ScrapingResult(
            search_criteria=self.search_criteria,
            flights=[flight_no_segments],
            total_results=1,
            success=True,
            execution_time=2.5
        )
        
        display_results(result)
        
        # Should still display the table with N/A values
        assert mock_console.print.call_count == 2


class TestSaveToJson:
    """Test save_to_json function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.search_criteria = SearchCriteria(
            origin="LAX",
            destination="NYC",
            departure_date=date(2025, 7, 1),
            return_date=date(2025, 7, 10),
            trip_type=TripType.ROUND_TRIP,
            max_results=50
        )
        
        self.segment = FlightSegment(
            airline="American Airlines",
            flight_number="AA123",
            departure_airport="LAX",
            arrival_airport="JFK",
            departure_time="09:00",
            arrival_time="17:30",
            duration="5h 30m",
            aircraft="Boeing 737"
        )
        
        self.flight = FlightOffer(
            price="$299",
            currency="USD",
            stops=0,
            total_duration="5h 30m",
            segments=[self.segment]
        )

    @patch('flight_scraper.cli.main.console')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_to_json_success(self, mock_file, mock_console):
        """Test successful JSON save."""
        result = ScrapingResult(
            search_criteria=self.search_criteria,
            flights=[self.flight],
            total_results=1,
            success=True,
            execution_time=2.5
        )
        
        save_to_json(result, "test.json")
        
        # Verify file was opened correctly
        mock_file.assert_called_once_with(Path("test.json"), 'w', encoding='utf-8')
        
        # Verify console message
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "Results saved to" in call_args

    @patch('flight_scraper.cli.main.console')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_to_json_content(self, mock_json_dump, mock_file, mock_console):
        """Test JSON content structure."""
        result = ScrapingResult(
            search_criteria=self.search_criteria,
            flights=[self.flight],
            total_results=1,
            success=True,
            execution_time=2.5
        )
        
        save_to_json(result, "test.json")
        
        # Verify json.dump was called
        mock_json_dump.assert_called_once()
        
        # Get the data that was passed to json.dump
        call_args = mock_json_dump.call_args[0][0]
        
        # Verify structure
        assert "search_criteria" in call_args
        assert "results" in call_args
        assert "flights" in call_args
        assert call_args["search_criteria"]["origin"] == "LAX"
        assert call_args["search_criteria"]["destination"] == "NYC"
        assert len(call_args["flights"]) == 1


class TestSaveToCsv:
    """Test save_to_csv function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.search_criteria = SearchCriteria(
            origin="LAX",
            destination="NYC",
            departure_date=date(2025, 7, 1),
            trip_type=TripType.ONE_WAY,
            max_results=50
        )
        
        self.segment = FlightSegment(
            airline="American Airlines",
            flight_number="AA123",
            departure_airport="LAX",
            arrival_airport="JFK",
            departure_time="09:00",
            arrival_time="17:30",
            duration="5h 30m",
            aircraft="Boeing 737"
        )
        
        self.flight = FlightOffer(
            price="$299",
            currency="USD",
            stops=0,
            total_duration="5h 30m",
            segments=[self.segment]
        )

    @patch('flight_scraper.cli.main.console')
    @patch('builtins.open', new_callable=mock_open)
    @patch('csv.writer')
    def test_save_to_csv_success(self, mock_csv_writer, mock_file, mock_console):
        """Test successful CSV save."""
        mock_writer = Mock()
        mock_csv_writer.return_value = mock_writer
        
        result = ScrapingResult(
            search_criteria=self.search_criteria,
            flights=[self.flight],
            total_results=1,
            success=True,
            execution_time=2.5
        )
        
        save_to_csv(result, "test.csv")
        
        # Verify file was opened correctly
        mock_file.assert_called_once_with(Path("test.csv"), 'w', newline='', encoding='utf-8')
        
        # Verify CSV writer was used correctly
        mock_writer.writerow.assert_called()
        assert mock_writer.writerow.call_count == 2  # Header + 1 flight row
        
        # Verify console message
        mock_console.print.assert_called_once()

    @patch('flight_scraper.cli.main.console')
    @patch('builtins.open', new_callable=mock_open)
    @patch('csv.writer')
    def test_save_to_csv_no_segments(self, mock_csv_writer, mock_file, mock_console):
        """Test CSV save with flight that has no segments."""
        mock_writer = Mock()
        mock_csv_writer.return_value = mock_writer
        
        flight_no_segments = FlightOffer(
            price="$299",
            currency="USD",
            stops=0,
            total_duration="5h 30m",
            segments=[]
        )
        
        result = ScrapingResult(
            search_criteria=self.search_criteria,
            flights=[flight_no_segments],
            total_results=1,
            success=True,
            execution_time=2.5
        )
        
        save_to_csv(result, "test.csv")
        
        # Should still write header and row with N/A values
        assert mock_writer.writerow.call_count == 2


class TestScrapeCommand:
    """Test the scrape CLI command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        
        self.mock_result = ScrapingResult(
            search_criteria=SearchCriteria(
                origin="LAX",
                destination="NYC",
                departure_date=date(2025, 7, 1),
                trip_type=TripType.ONE_WAY,
                max_results=50
            ),
            flights=[],
            total_results=0,
            success=True,
            execution_time=2.5
        )

    @patch('flight_scraper.cli.main.scrape_flights_async')
    @patch('flight_scraper.cli.main.setup_logging')
    @patch('flight_scraper.cli.main.display_results')
    def test_scrape_basic_command(self, mock_display, mock_setup_logging, mock_scrape_async):
        """Test basic scrape command."""
        mock_scrape_async.return_value = self.mock_result
        
        result = self.runner.invoke(app, [
            "scrape", "LAX", "NYC", "2025-07-01"
        ])
        
        assert result.exit_code == 0
        mock_setup_logging.assert_called_once()
        mock_scrape_async.assert_called_once()
        mock_display.assert_called_once()

    @patch('flight_scraper.cli.main.scrape_flights_async')
    @patch('flight_scraper.cli.main.setup_logging')
    @patch('flight_scraper.cli.main.display_results')
    def test_scrape_with_return_date(self, mock_display, mock_setup_logging, mock_scrape_async):
        """Test scrape command with return date."""
        mock_scrape_async.return_value = self.mock_result
        
        result = self.runner.invoke(app, [
            "scrape", "LAX", "NYC", "2025-07-01", "--return", "2025-07-10"
        ])
        
        assert result.exit_code == 0
        mock_scrape_async.assert_called_once()
        
        # Verify return date was parsed correctly
        call_args = mock_scrape_async.call_args
        assert call_args[1]['return_date'] == date(2025, 7, 10)

    @patch('flight_scraper.cli.main.scrape_flights_async')
    @patch('flight_scraper.cli.main.setup_logging')
    @patch('flight_scraper.cli.main.save_to_json')
    def test_scrape_save_json(self, mock_save_json, mock_setup_logging, mock_scrape_async):
        """Test scrape command with JSON output."""
        mock_scrape_async.return_value = self.mock_result
        
        result = self.runner.invoke(app, [
            "scrape", "LAX", "NYC", "2025-07-01",
            "--format", "json", "--output", "test.json"
        ])
        
        assert result.exit_code == 0
        mock_save_json.assert_called_once_with(self.mock_result, "test.json")

    @patch('flight_scraper.cli.main.scrape_flights_async')
    @patch('flight_scraper.cli.main.setup_logging')
    @patch('flight_scraper.cli.main.save_to_csv')
    def test_scrape_save_csv(self, mock_save_csv, mock_setup_logging, mock_scrape_async):
        """Test scrape command with CSV output."""
        mock_scrape_async.return_value = self.mock_result
        
        result = self.runner.invoke(app, [
            "scrape", "LAX", "NYC", "2025-07-01",
            "--format", "csv", "--output", "test.csv"
        ])
        
        assert result.exit_code == 0
        mock_save_csv.assert_called_once_with(self.mock_result, "test.csv")

    @patch('flight_scraper.cli.main.scrape_flights_async')
    @patch('flight_scraper.cli.main.setup_logging')
    @patch('flight_scraper.cli.main.save_to_json')
    @patch('flight_scraper.cli.main.datetime')
    def test_scrape_auto_filename_json(self, mock_datetime, mock_save_json, mock_setup_logging, mock_scrape_async):
        """Test scrape command with auto-generated JSON filename."""
        mock_scrape_async.return_value = self.mock_result
        mock_datetime.now.return_value.strftime.return_value = "20250701_120000"
        
        result = self.runner.invoke(app, [
            "scrape", "LAX", "NYC", "2025-07-01", "--format", "json"
        ])
        
        assert result.exit_code == 0
        mock_save_json.assert_called_once()
        
        # Check the auto-generated filename
        call_args = mock_save_json.call_args[0]
        assert "flights_LAX_NYC_20250701_120000.json" in call_args[1]

    @patch('flight_scraper.cli.main.scrape_flights_async')
    @patch('flight_scraper.cli.main.setup_logging')
    @patch('flight_scraper.cli.main.save_to_csv')
    @patch('flight_scraper.cli.main.datetime')
    def test_scrape_auto_filename_csv(self, mock_datetime, mock_save_csv, mock_setup_logging, mock_scrape_async):
        """Test scrape command with auto-generated CSV filename."""
        mock_scrape_async.return_value = self.mock_result
        mock_datetime.now.return_value.strftime.return_value = "20250701_120000"
        
        result = self.runner.invoke(app, [
            "scrape", "LAX", "NYC", "2025-07-01", "--format", "csv"
        ])
        
        assert result.exit_code == 0
        mock_save_csv.assert_called_once()

    def test_scrape_invalid_date_format(self):
        """Test scrape command with invalid date format."""
        result = self.runner.invoke(app, [
            "scrape", "LAX", "NYC", "invalid-date"
        ])
        
        assert result.exit_code == 1
        assert "Invalid date format" in result.stdout

    @patch('flight_scraper.cli.main.scrape_flights_async')
    @patch('flight_scraper.cli.main.setup_logging')
    def test_scrape_with_all_options(self, mock_setup_logging, mock_scrape_async):
        """Test scrape command with all options."""
        mock_scrape_async.return_value = self.mock_result
        
        result = self.runner.invoke(app, [
            "scrape", "LAX", "NYC", "2025-07-01",
            "--return", "2025-07-10",
            "--max-results", "25",
            "--format", "table",
            "--headless",
            "--verbose"
        ])
        
        assert result.exit_code == 0
        
        # Verify all parameters were passed correctly
        call_args = mock_scrape_async.call_args[1]
        assert call_args['origin'] == "LAX"
        assert call_args['destination'] == "NYC"
        assert call_args['departure_date'] == date(2025, 7, 1)
        assert call_args['return_date'] == date(2025, 7, 10)
        assert call_args['max_results'] == 25
        assert call_args['headless'] is True

    @patch('flight_scraper.cli.main.scrape_flights_async')
    @patch('flight_scraper.cli.main.setup_logging')
    def test_scrape_with_verbose_logging(self, mock_setup_logging, mock_scrape_async):
        """Test scrape command with verbose logging."""
        mock_scrape_async.return_value = self.mock_result
        
        with patch('flight_scraper.cli.main.logger') as mock_logger:
            result = self.runner.invoke(app, [
                "scrape", "LAX", "NYC", "2025-07-01", "--verbose"
            ])
            
            assert result.exit_code == 0
            mock_logger.remove.assert_called_once()
            mock_logger.add.assert_called_once()

    @patch('flight_scraper.cli.main.scrape_flights_async')
    @patch('flight_scraper.cli.main.setup_logging')
    def test_scrape_unsupported_output_format(self, mock_setup_logging, mock_scrape_async):
        """Test scrape command with unsupported output format."""
        mock_scrape_async.return_value = self.mock_result
        
        result = self.runner.invoke(app, [
            "scrape", "LAX", "NYC", "2025-07-01",
            "--format", "xml", "--output", "test.xml"
        ])
        
        assert result.exit_code == 0
        assert "Unsupported output format" in result.stdout

    @patch('flight_scraper.cli.main.scrape_flights_async')
    @patch('flight_scraper.cli.main.setup_logging')
    def test_scrape_file_extension_json(self, mock_setup_logging, mock_scrape_async):
        """Test scrape command with .json file extension."""
        mock_scrape_async.return_value = self.mock_result
        
        with patch('flight_scraper.cli.main.save_to_json') as mock_save_json:
            result = self.runner.invoke(app, [
                "scrape", "LAX", "NYC", "2025-07-01", "--output", "test.json"
            ])
            
            assert result.exit_code == 0
            mock_save_json.assert_called_once()

    @patch('flight_scraper.cli.main.scrape_flights_async')
    @patch('flight_scraper.cli.main.setup_logging')
    def test_scrape_file_extension_csv(self, mock_setup_logging, mock_scrape_async):
        """Test scrape command with .csv file extension."""
        mock_scrape_async.return_value = self.mock_result
        
        with patch('flight_scraper.cli.main.save_to_csv') as mock_save_csv:
            result = self.runner.invoke(app, [
                "scrape", "LAX", "NYC", "2025-07-01", "--output", "test.csv"
            ])
            
            assert result.exit_code == 0
            mock_save_csv.assert_called_once()

    @patch('flight_scraper.cli.main.scrape_flights_async')
    @patch('flight_scraper.cli.main.setup_logging')
    def test_scrape_exception_handling(self, mock_setup_logging, mock_scrape_async):
        """Test scrape command exception handling."""
        mock_scrape_async.side_effect = Exception("Network error")
        
        result = self.runner.invoke(app, [
            "scrape", "LAX", "NYC", "2025-07-01"
        ])
        
        assert result.exit_code == 1
        assert "Error:" in result.stdout


class TestExampleCommand:
    """Test the example CLI command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch('flight_scraper.cli.main.console')
    def test_example_command(self, mock_console):
        """Test example command."""
        result = self.runner.invoke(app, ["example"])
        
        assert result.exit_code == 0
        
        # Should print multiple example commands
        assert mock_console.print.call_count >= 8  # Title + multiple examples
