"""
Simplified MCP Server for Google Flights Scraper.
This module provides a clean, maintainable MCP server implementation.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, Optional

from fastmcp import FastMCP
from loguru import logger

from ..core.scraper import scrape_flights_async
from ..core.models import TripType, SearchCriteria
from ..utils import normalize_airport_code

# Initialize FastMCP server
mcp = FastMCP("Google Flights Scraper")

# Airport mappings for user convenience
AIRPORT_MAPPINGS = {
    "new york": "JFK", "nyc": "JFK", "los angeles": "LAX", "la": "LAX",
    "san francisco": "SFO", "sf": "SFO", "chicago": "ORD", "miami": "MIA",
    "boston": "BOS", "seattle": "SEA", "denver": "DEN", "atlanta": "ATL",
    "dallas": "DFW", "houston": "IAH", "phoenix": "PHX", "philadelphia": "PHL",
    "detroit": "DTW", "minneapolis": "MSP", "orlando": "MCO", "las vegas": "LAS",
    "vegas": "LAS", "washington": "DCA", "dc": "DCA", "london": "LHR",
    "paris": "CDG", "tokyo": "NRT", "singapore": "SIN", "sydney": "SYD",
    "toronto": "YYZ", "vancouver": "YVR", "mexico city": "MEX", "cancun": "CUN"
}

def normalize_airport_input(airport_input: str) -> str:
    """Normalize airport input to proper airport code."""
    if not airport_input:
        return ""
    
    airport_clean = airport_input.strip().lower()
    
    # Check if already a valid 3-letter code
    if len(airport_clean) == 3 and airport_clean.isalpha():
        return airport_clean.upper()
    
    # Check airport mappings
    if airport_clean in AIRPORT_MAPPINGS:
        return AIRPORT_MAPPINGS[airport_clean]
    
    # Fallback to normalize_airport_code utility
    return normalize_airport_code(airport_input)

def serialize_for_json(obj: Any) -> Any:
    """Convert objects to JSON-serializable format."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, 'model_dump'):
        return obj.model_dump()
    elif hasattr(obj, 'dict'):
        return obj.dict()
    else:
        return str(obj)

@mcp.tool
async def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    trip_type: str = "one_way",
    max_results: int = 10,
    headless: bool = True
) -> Dict[str, Any]:
    """Search for flights using Google Flights scraper."""
    start_time = datetime.now()
    
    try:
        logger.info(f"Flight search: {origin} -> {destination} on {departure_date}")
        
        # Normalize airport codes
        origin_code = normalize_airport_input(origin)
        destination_code = normalize_airport_input(destination)
        
        if not origin_code or not destination_code:
            return {
                "success": False,
                "error": "Invalid airport codes provided"
            }
        
        # Parse dates
        try:
            departure_date_obj = datetime.strptime(departure_date, "%Y-%m-%d").date()
            return_date_obj = None
            if return_date:
                return_date_obj = datetime.strptime(return_date, "%Y-%m-%d").date()
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid date format: {str(e)}. Use YYYY-MM-DD format."
            }
        
        # Validate trip type
        if trip_type not in ["one_way", "round_trip"]:
            return {
                "success": False,
                "error": "Invalid trip_type. Must be 'one_way' or 'round_trip'"
            }
        
        # Perform flight search
        result = await scrape_flights_async(
            origin=origin_code,
            destination=destination_code,
            departure_date=departure_date_obj,
            return_date=return_date_obj,
            max_results=min(max_results, 50),
            headless=headless
        )
        
        # Serialize flight data
        flights_data = []
        for flight in result.flights:
            flight_dict = flight.model_dump()
            flight_dict["scraped_at"] = serialize_for_json(flight.scraped_at)
            for segment in flight_dict["segments"]:
                if "scraped_at" in segment:
                    segment["scraped_at"] = serialize_for_json(segment.get("scraped_at"))
            flights_data.append(flight_dict)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        response = {
            "success": result.success,
            "search_criteria": {
                "origin": result.search_criteria.origin,
                "destination": result.search_criteria.destination,
                "departure_date": result.search_criteria.departure_date.isoformat(),
                "return_date": result.search_criteria.return_date.isoformat() if result.search_criteria.return_date else None,
                "trip_type": result.search_criteria.trip_type.value,
                "max_results": result.search_criteria.max_results
            },
            "flights": flights_data,
            "total_results": result.total_results,
            "scraped_at": serialize_for_json(result.scraped_at),
            "execution_time": result.execution_time,
            "mcp_execution_time": execution_time
        }
        
        if not result.success and result.error_message:
            response["error"] = result.error_message
        
        logger.info(f"Flight search completed: {result.total_results} flights in {execution_time:.2f}s")
        return response
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        error_msg = f"Flight search failed: {str(e)}"
        logger.error(error_msg)
        
        return {
            "success": False,
            "error": error_msg,
            "execution_time": execution_time
        }

@mcp.tool
async def get_airport_info(query: str) -> Dict[str, Any]:
    """Get airport information and normalize queries."""
    try:
        logger.info(f"Airport info lookup: '{query}'")
        
        original_query = query
        normalized_code = normalize_airport_input(query)
        
        # Check for city matches
        query_lower = query.lower().strip()
        matched_city = None
        for city, code in AIRPORT_MAPPINGS.items():
            if query_lower == city or query_lower in city:
                matched_city = city
                break
        
        result = {
            "success": True,
            "original_query": original_query,
            "normalized_code": normalized_code,
            "matched_city": matched_city,
            "is_valid_code": len(normalized_code) == 3 and normalized_code.isalpha(),
            "suggestions": []
        }
        
        # Add suggestions for partial matches
        if not result["is_valid_code"] and not matched_city:
            suggestions = []
            for city, code in AIRPORT_MAPPINGS.items():
                if query_lower in city or city in query_lower:
                    suggestions.append({"city": city, "code": code})
            result["suggestions"] = suggestions[:5]
        
        logger.info(f"Airport lookup completed: '{query}' -> '{normalized_code}'")
        return result
        
    except Exception as e:
        error_msg = f"Airport info lookup failed: {str(e)}"
        logger.error(error_msg)
        
        return {
            "success": False,
            "error": error_msg,
            "original_query": query
        }

@mcp.tool
async def get_scraper_status() -> Dict[str, Any]:
    """Check scraper health and configuration."""
    try:
        logger.info("Checking scraper status")
        
        # Test browser initialization
        from ..core.scraper import GoogleFlightsScraper
        
        browser_test_success = True
        browser_error = None
        
        try:
            async with GoogleFlightsScraper(headless=True) as scraper:
                await asyncio.sleep(0.1)
        except Exception as e:
            browser_test_success = False
            browser_error = str(e)
        
        status = {
            "success": True,
            "scraper_status": {
                "browser_test": browser_test_success,
                "browser_error": browser_error,
                "available_tools": ["search_flights", "get_airport_info", "get_scraper_status"]
            },
            "supported_features": {
                "trip_types": ["one_way", "round_trip"],
                "max_results_limit": 50,
                "async_operation": True
            },
            "airport_mappings": {
                "total_cities": len(AIRPORT_MAPPINGS),
                "sample_mappings": dict(list(AIRPORT_MAPPINGS.items())[:10])
            },
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("Scraper status check completed")
        return status
        
    except Exception as e:
        error_msg = f"Scraper status check failed: {str(e)}"
        logger.error(error_msg)
        
        return {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }

def create_mcp_server() -> FastMCP:
    """Create and return the configured MCP server instance."""
    logger.info("Creating MCP server for Google Flights scraper")
    return mcp

async def run_server(host: str = "localhost", port: int = 8000, use_stdio: bool = False) -> None:
    """Run the MCP server."""
    try:
        if use_stdio:
            logger.info("Starting MCP server in stdio mode")
            await mcp.run()
        else:
            logger.info(f"Starting MCP server on {host}:{port}")
            await mcp.run(host=host, port=port)
    except Exception as e:
        logger.error(f"Failed to start MCP server: {str(e)}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Google Flights MCP Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--stdio", action="store_true", help="Use stdio mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logger.remove()
        logger.add(lambda msg: print(msg, end=""), level="DEBUG")
    
    logger.info("Google Flights MCP Server starting...")
    
    try:
        asyncio.run(run_server(host=args.host, port=args.port, use_stdio=args.stdio))
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed: {str(e)}")