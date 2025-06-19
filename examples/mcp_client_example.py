#!/usr/bin/env python3
"""
Google Flights MCP Client Example

This example demonstrates how to connect to and use the Google Flights MCP server
from a Python client application.

Prerequisites:
1. Install the flight scraper package: pip install -e .
2. Start the MCP server: python run_mcp_server.py
3. Run this example: python examples/mcp_client_example.py
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

try:
    import httpx
except ImportError:
    print("Please install httpx: pip install httpx")
    exit(1)


class FlightsMCPClient:
    """Simple MCP client for the Google Flights server."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=120.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool on the server."""
        url = f"{self.base_url}/call_tool"
        payload = {"name": tool_name, "arguments": arguments}

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            return {"success": False, "error": f"Network error: {e}"}
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP error {e.response.status_code}: {e.response.text}",
            }

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        max_results: int = 5,
        headless: bool = True,
    ) -> Dict[str, Any]:
        """Search for flights between two airports."""
        arguments = {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "max_results": max_results,
            "headless": headless,
        }

        if return_date:
            arguments["return_date"] = return_date
            arguments["trip_type"] = "round_trip"
        else:
            arguments["trip_type"] = "one_way"

        return await self.call_tool("search_flights", arguments)

    async def get_scraper_status(self) -> Dict[str, Any]:
        """Get scraper status and health information."""
        return await self.call_tool("get_scraper_status", {})


async def demonstrate_scraper_status():
    """Demonstrate scraper status check."""
    print("\n" + "=" * 60)
    print("🔧 SCRAPER STATUS CHECK")
    print("=" * 60)

    async with FlightsMCPClient() as client:
        result = await client.get_scraper_status()

        if result.get("success"):
            status = result["scraper_status"]
            config = result["configuration"]
            features = result["supported_features"]

            print(f"\n✅ Scraper Status:")
            print(f"  🌐 Browser Test: {'✅ Passed' if status['browser_test'] else '❌ Failed'}")
            if status.get("browser_error"):
                print(f"  ⚠️  Browser Error: {status['browser_error']}")
            print(f"  🛠️  Available Tools: {', '.join(status['available_tools'])}")

            print(f"\n⚙️  Configuration:")
            print(f"  ⏱️  Timeout: {config['timeout']}ms")
            print(f"  🧭 Navigation Timeout: {config['navigation_timeout']}ms")
            print(f"  🔄 Retry Attempts: {config['retry_attempts']}")
            print(f"  👻 Default Headless: {config['default_headless']}")

            print(f"\n🚀 Supported Features:")
            print(f"  ✈️  Trip Types: {', '.join(features['trip_types'])}")
            print(f"  📊 Max Results: {features['max_results_limit']}")
            print(f"  ⚡ Async Operation: {features['async_operation']}")
        else:
            print(f"❌ Status check failed: {result.get('error', 'Unknown error')}")


async def demonstrate_flight_search():
    """Demonstrate flight search functionality."""
    print("\n" + "=" * 60)
    print("🔍 FLIGHT SEARCH EXAMPLES")
    print("=" * 60)

    async with FlightsMCPClient() as client:
        # Get tomorrow's date for the search
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        next_week = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")

        # Example 1: One-way search
        print(f"\n🛫 One-way flight search: JFK → LAX on {tomorrow}")
        result = await client.search_flights(
            origin="JFK", destination="LAX", departure_date=tomorrow, max_results=3
        )

        if result.get("success"):
            flights = result.get("flights", [])
            print(
                f"  ✅ Found {len(flights)} flights (execution time: {result.get('execution_time', 0):.1f}s)"
            )

            for i, flight in enumerate(flights[:2], 1):  # Show first 2 flights
                print(f"\n  Flight {i}:")
                print(f"    💰 Price: {flight.get('price', 'N/A')}")
                print(f"    ⏱️  Duration: {flight.get('total_duration', 'N/A')}")
                print(f"    🛑 Stops: {flight.get('stops', 'N/A')}")

                segments = flight.get("segments", [])
                if segments:
                    seg = segments[0]
                    print(f"    🛩️  Airline: {seg.get('airline', 'N/A')}")
                    print(f"    🕐 Departure: {seg.get('departure_time', 'N/A')}")
                    print(f"    🕐 Arrival: {seg.get('arrival_time', 'N/A')}")
        else:
            print(f"  ❌ Search failed: {result.get('error', 'Unknown error')}")

        # Example 2: Round-trip search (commented out for demo speed)
        print(f"\n🔄 Round-trip search would be: JFK ⇄ LAX ({tomorrow} - {next_week})")
        print("  (Skipped for demo - uncomment to test)")

        # Uncomment to test round-trip search:
        # result = await client.search_flights(
        #     origin="JFK",
        #     destination="LAX",
        #     departure_date=tomorrow,
        #     return_date=next_week,
        #     max_results=2
        # )


async def demonstrate_error_handling():
    """Demonstrate error handling scenarios."""
    print("\n" + "=" * 60)
    print("🚨 ERROR HANDLING EXAMPLES")
    print("=" * 60)

    async with FlightsMCPClient() as client:
        # Test invalid date format
        print("\n❌ Testing invalid date format:")
        result = await client.search_flights("JFK", "LAX", "invalid-date")
        print(f"  Result: {result.get('error', 'No error message')}")

        # Test connection to wrong port
        print("\n❌ Testing connection error:")
        wrong_client = FlightsMCPClient("http://localhost:9999")
        async with wrong_client as client:
            result = await client.get_scraper_status()
            print(f"  Result: {result.get('error', 'No error message')}")


async def main():
    """Run all demonstration examples."""
    print("🚀 Google Flights MCP Client Demonstration")
    print("=" * 60)
    print("This example demonstrates the MCP server functionality.")
    print("Make sure the MCP server is running: python run_mcp_server.py")

    try:
        await demonstrate_scraper_status()
        await demonstrate_flight_search()
        await demonstrate_error_handling()

        print("\n" + "=" * 60)
        print("✅ MCP CLIENT DEMONSTRATION COMPLETED")
        print("=" * 60)
        print("\n💡 Next Steps:")
        print("  • Integrate these patterns into your application")
        print("  • Check the MCP_SERVER_GUIDE.md for more details")
        print("  • Explore additional configuration options")

    except KeyboardInterrupt:
        print("\n\n⏹️  Demonstration interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demonstration failed: {e}")
        print("   Make sure the MCP server is running on localhost:8000")


if __name__ == "__main__":
    # Install httpx if needed
    try:
        import httpx

        asyncio.run(main())
    except ImportError:
        print("❌ Missing dependency: httpx")
        print("Install with: pip install httpx")
        exit(1)
