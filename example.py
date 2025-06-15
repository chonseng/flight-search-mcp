"""Example usage of the Google Flights scraper."""

import asyncio
from datetime import date, timedelta
from scraper import scrape_flights_async
from utils import setup_logging


async def main():
    """Run example flight searches."""
    setup_logging()
    
    print("🛫 Google Flights Scraper Example")
    print("=" * 40)
    
    # Example 1: One-way flight
    print("\n1. One-way flight: LAX to NYC")
    departure_date = date.today() + timedelta(days=30)  # 30 days from now
    
    result = await scrape_flights_async(
        origin="LAX",
        destination="NYC", 
        departure_date=departure_date,
        max_results=5
    )
    
    if result.success:
        print(f"✅ Found {len(result.flights)} flights")
        for i, flight in enumerate(result.flights[:3], 1):
            segment = flight.segments[0] if flight.segments else None
            print(f"  {i}. {segment.airline if segment else 'N/A'} - {flight.price} ({flight.stops} stops)")
    else:
        print(f"❌ Search failed: {result.error_message}")
    
    print("\n" + "-" * 40)
    
    # Example 2: Round-trip flight
    print("\n2. Round-trip flight: SFO to LAX")
    departure_date = date.today() + timedelta(days=45)
    return_date = departure_date + timedelta(days=3)
    
    result = await scrape_flights_async(
        origin="SFO",
        destination="LAX",
        departure_date=departure_date,
        return_date=return_date,
        max_results=5
    )
    
    if result.success:
        print(f"✅ Found {len(result.flights)} round-trip flights")
        for i, flight in enumerate(result.flights[:3], 1):
            segment = flight.segments[0] if flight.segments else None
            print(f"  {i}. {segment.airline if segment else 'N/A'} - {flight.price} ({flight.stops} stops)")
    else:
        print(f"❌ Search failed: {result.error_message}")
    
    print("\n🎉 Example completed!")


if __name__ == "__main__":
    asyncio.run(main())