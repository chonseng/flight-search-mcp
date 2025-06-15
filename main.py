"""Main entry point for the Google Flights scraper package.

This file provides backward compatibility and easy access to the CLI interface.
"""

from flight_scraper.cli.main import app

if __name__ == "__main__":
    app()