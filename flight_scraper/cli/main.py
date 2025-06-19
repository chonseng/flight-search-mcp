"""Main CLI interface for the Google Flights scraper."""

import asyncio
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from loguru import logger
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..core.models import ScrapingResult
from ..core.scraper import scrape_flights_async
from ..utils import setup_logging

app = typer.Typer(help="Google Flights Scraper - Extract flight information from Google Flights")
console = Console()


def display_results(result: ScrapingResult) -> None:
    """Display scraping results in a formatted table."""
    if not result.success:
        console.print(f"[red]Scraping failed: {result.error_message}[/red]")
        return

    if not result.flights:
        console.print("[yellow]No flights found for the given criteria.[/yellow]")
        return

    # Create results table
    table = Table(
        title=f"Flight Results: {result.search_criteria.origin} → {result.search_criteria.destination}"
    )
    table.add_column("Airline", style="cyan")
    table.add_column("Departure", style="green")
    table.add_column("Arrival", style="green")
    table.add_column("Duration", style="yellow")
    table.add_column("Stops", style="blue")
    table.add_column("Price", style="red")

    for flight in result.flights:
        segment = flight.segments[0] if flight.segments else None
        table.add_row(
            segment.airline if segment else "N/A",
            segment.departure_time if segment else "N/A",
            segment.arrival_time if segment else "N/A",
            flight.total_duration,
            str(flight.stops),
            flight.price,
        )

    console.print(table)
    console.print(
        f"\n[green]Found {result.total_results} flights in {result.execution_time:.2f} seconds[/green]"
    )


def save_to_json(result: ScrapingResult, filename: str) -> None:
    """Save results to JSON file."""
    output_path = Path(filename)

    # Convert to dict for JSON serialization
    data = {
        "search_criteria": {
            "origin": result.search_criteria.origin,
            "destination": result.search_criteria.destination,
            "departure_date": result.search_criteria.departure_date.isoformat(),
            "return_date": (
                result.search_criteria.return_date.isoformat()
                if result.search_criteria.return_date
                else None
            ),
            "trip_type": result.search_criteria.trip_type.value,
            "max_results": result.search_criteria.max_results,
        },
        "results": {
            "success": result.success,
            "total_results": result.total_results,
            "execution_time": result.execution_time,
            "scraped_at": result.scraped_at.isoformat(),
            "error_message": result.error_message,
        },
        "flights": [],
    }

    for flight in result.flights:
        flight_data = {
            "price": flight.price,
            "currency": flight.currency,
            "stops": flight.stops,
            "total_duration": flight.total_duration,
            "segments": [],
        }

        for segment in flight.segments:
            segment_data = {
                "airline": segment.airline,
                "flight_number": segment.flight_number,
                "departure_airport": segment.departure_airport,
                "arrival_airport": segment.arrival_airport,
                "departure_time": segment.departure_time,
                "arrival_time": segment.arrival_time,
                "duration": segment.duration,
                "aircraft": segment.aircraft,
            }
            flight_data["segments"].append(segment_data)

        data["flights"].append(flight_data)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    console.print(f"[green]Results saved to {output_path}[/green]")


def save_to_csv(result: ScrapingResult, filename: str) -> None:
    """Save results to CSV file."""
    output_path = Path(filename)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Write header
        writer.writerow(
            [
                "Airline",
                "Departure Time",
                "Arrival Time",
                "Duration",
                "Stops",
                "Price",
                "Currency",
                "Departure Airport",
                "Arrival Airport",
            ]
        )

        # Write flight data
        for flight in result.flights:
            segment = flight.segments[0] if flight.segments else None
            writer.writerow(
                [
                    segment.airline if segment else "N/A",
                    segment.departure_time if segment else "N/A",
                    segment.arrival_time if segment else "N/A",
                    flight.total_duration,
                    flight.stops,
                    flight.price,
                    flight.currency,
                    segment.departure_airport if segment else "N/A",
                    segment.arrival_airport if segment else "N/A",
                ]
            )

    console.print(f"[green]Results saved to {output_path}[/green]")


@app.command()
def scrape(
    origin: str = typer.Argument(..., help="Origin airport code (e.g., LAX, JFK)"),
    destination: str = typer.Argument(..., help="Destination airport code (e.g., NYC, SFO)"),
    departure_date: str = typer.Argument(..., help="Departure date (YYYY-MM-DD)"),
    return_date: Optional[str] = typer.Option(
        None, "--return", "-r", help="Return date for round-trip (YYYY-MM-DD)"
    ),
    max_results: int = typer.Option(50, "--max-results", "-m", help="Maximum number of results"),
    output_format: str = typer.Option(
        "table", "--format", "-f", help="Output format: table, json, csv"
    ),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    headless: bool = typer.Option(False, "--headless", help="Run browser in headless mode"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """Scrape flights from Google Flights."""

    # Setup logging
    setup_logging()
    if verbose:
        logger.remove()
        logger.add(lambda msg: print(msg, end=""), level="DEBUG", colorize=True)

    try:
        # Parse dates
        dep_date = datetime.strptime(departure_date, "%Y-%m-%d").date()
        ret_date = datetime.strptime(return_date, "%Y-%m-%d").date() if return_date else None

        console.print(f"[blue]Searching flights: {origin} → {destination}[/blue]")
        console.print(f"[blue]Departure: {dep_date}[/blue]")
        if ret_date:
            console.print(f"[blue]Return: {ret_date}[/blue]")

        # Run scraping with progress indicator
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Scraping flights...", total=None)

            # Run async scraping
            result = asyncio.run(
                scrape_flights_async(
                    origin=origin,
                    destination=destination,
                    departure_date=dep_date,
                    return_date=ret_date,
                    max_results=max_results,
                    headless=headless,
                )
            )

            progress.update(task, completed=True)

        # Display results
        if output_format == "table" or not output_file:
            display_results(result)

        # Save to file if requested
        if output_file:
            if output_format == "json" or output_file.endswith(".json"):
                save_to_json(result, output_file)
            elif output_format == "csv" or output_file.endswith(".csv"):
                save_to_csv(result, output_file)
            else:
                console.print("[red]Unsupported output format. Use 'json' or 'csv'.[/red]")

        # Generate default filename if format specified but no file
        elif output_format in ["json", "csv"]:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"flights_{origin}_{destination}_{timestamp}.{output_format}"

            if output_format == "json":
                save_to_json(result, default_filename)
            else:
                save_to_csv(result, default_filename)

    except ValueError as e:
        console.print(f"[red]Invalid date format. Use YYYY-MM-DD: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Scraping error: {e}")
        raise typer.Exit(1)


@app.command()
def example() -> None:
    """Show usage examples."""
    console.print("[bold green]Google Flights Scraper Examples[/bold green]\n")

    console.print("[bold]Basic one-way search:[/bold]")
    console.print("python main.py cli scrape LAX NYC 2025-07-01\n")

    console.print("[bold]Round-trip search:[/bold]")
    console.print("python main.py cli scrape LAX NYC 2025-07-01 --return 2025-07-10\n")

    console.print("[bold]Save results to JSON:[/bold]")
    console.print(
        "python main.py cli scrape LAX NYC 2025-07-01 --format json --output flights.json\n"
    )

    console.print("[bold]Save results to CSV:[/bold]")
    console.print(
        "python main.py cli scrape LAX NYC 2025-07-01 --format csv --output flights.csv\n"
    )

    console.print("[bold]Limit results and run headless:[/bold]")
    console.print("python main.py cli scrape LAX NYC 2025-07-01 --max-results 20 --headless\n")

    console.print("[bold]Verbose logging:[/bold]")
    console.print("python main.py cli scrape LAX NYC 2025-07-01 --verbose\n")

    console.print("[bold]Alternative - Using package directly:[/bold]")
    console.print("python -m flight_scraper.cli.main scrape LAX NYC 2025-07-01\n")


if __name__ == "__main__":
    app()
