"""Command Line Interface for the Google Flights scraper.

This module provides a user-friendly CLI interface using Typer with Rich formatting
for displaying flight search results and managing output formats.
"""

from .main import app

__all__ = ["app"]
