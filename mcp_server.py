#!/usr/bin/env python3
"""
Simple MCP Server for Google Flights Scraper.
Provides flight scraping capabilities via MCP protocol in stdio mode.
"""

import json
import sys
import asyncio
from datetime import datetime
from typing import Any, Dict

from flight_scraper.core.scraper import scrape_flights_async
from flight_scraper.core.models import TripType

# Airport code mappings for common cities - helps normalize user input
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
    """
    Normalize airport input to proper airport code.
    Handles both city names and airport codes.
    """
    if not airport_input:
        return ""
    
    airport_clean = airport_input.strip().lower()
    
    # Check if it's already a valid 3-letter code
    if len(airport_clean) == 3 and airport_clean.isalpha():
        return airport_clean.upper()
    
    # Check airport mappings for city names
    if airport_clean in AIRPORT_MAPPINGS:
        return AIRPORT_MAPPINGS[airport_clean]
    
    # Fallback to uppercase
    return airport_input.upper()

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

async def search_flights_impl(
    origin: str, destination: str, departure_date: str,
    return_date: str = None, trip_type: str = "one_way",
    max_results: int = 10, headless: bool = True
) -> Dict[str, Any]:
    """
    Core flight search implementation.
    This is the main function that performs the actual flight scraping.
    """
    start_time = datetime.now()
    
    try:
        # Normalize airport codes to handle city names
        origin_code = normalize_airport_input(origin)
        destination_code = normalize_airport_input(destination)
        
        if not origin_code or not destination_code:
            return {
                "success": False,
                "error": "Invalid airport codes provided"
            }
        
        # Parse and validate dates
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
        
        # Perform the actual flight scraping
        result = await scrape_flights_async(
            origin=origin_code,
            destination=destination_code,
            departure_date=departure_date_obj,
            return_date=return_date_obj,
            max_results=min(max_results, 50),  # Cap at 50 for performance
            headless=headless
        )
        
        # Convert flight results to JSON-serializable format
        flights_data = []
        for flight in result.flights:
            flight_dict = flight.model_dump()
            flight_dict["scraped_at"] = serialize_for_json(flight.scraped_at)
            for segment in flight_dict["segments"]:
                if "scraped_at" in segment:
                    segment["scraped_at"] = serialize_for_json(segment["scraped_at"])
            flights_data.append(flight_dict)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Build response with all relevant data
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
            "execution_time": result.execution_time
        }
        
        if not result.success and result.error_message:
            response["error"] = result.error_message
        
        return response
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        return {
            "success": False,
            "error": f"Flight search failed: {str(e)}",
            "execution_time": execution_time
        }

async def get_airport_info_impl(query: str) -> Dict[str, Any]:
    """
    Get airport information and normalize airport queries.
    Helps users understand how their input will be processed.
    """
    try:
        original_query = query
        normalized_code = normalize_airport_input(query)
        
        # Check if query matches any city in our mappings
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
        
        # Provide suggestions for partial matches
        if not result["is_valid_code"] and not matched_city:
            suggestions = []
            for city, code in AIRPORT_MAPPINGS.items():
                if query_lower in city or city in query_lower:
                    suggestions.append({"city": city, "code": code})
            result["suggestions"] = suggestions[:5]  # Limit to 5 suggestions
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Airport info lookup failed: {str(e)}",
            "original_query": query
        }

async def get_scraper_status_impl() -> Dict[str, Any]:
    """
    Check scraper health and configuration.
    Useful for debugging browser/scraper issues.
    """
    try:
        from flight_scraper.core.scraper import GoogleFlightsScraper
        
        # Test browser initialization
        browser_test_success = True
        browser_error = None
        
        try:
            async with GoogleFlightsScraper(headless=True) as scraper:
                await asyncio.sleep(0.1)  # Simple test
        except Exception as e:
            browser_test_success = False
            browser_error = str(e)
        
        return {
            "success": True,
            "scraper_status": {
                "browser_test": browser_test_success,
                "browser_error": browser_error
            },
            "available_tools": ["search_flights", "get_airport_info", "get_scraper_status"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Scraper status check failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# MCP Protocol Helper Functions
def create_error_response(request_id: str, error_code: int, message: str) -> Dict[str, Any]:
    """Create a standard MCP error response."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": error_code, "message": message}
    }

def create_success_response(request_id: str, result: Any) -> Dict[str, Any]:
    """Create a standard MCP success response."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result
    }

async def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle incoming MCP requests.
    This is the main request router for the MCP protocol.
    """
    try:
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        # Handle MCP initialization
        if method == "initialize":
            return create_success_response(request_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "google-flights", "version": "1.0.0"}
            })

        elif method == "notifications/initialized":
            return None  # No response needed for notifications

        # List available tools
        elif method == "tools/list":
            return create_success_response(request_id, {
                "tools": [
                    {
                        "name": "search_flights",
                        "description": "Search for flights between airports",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "origin": {"type": "string", "description": "Origin airport code or city"},
                                "destination": {"type": "string", "description": "Destination airport code or city"},
                                "departure_date": {"type": "string", "description": "Departure date (YYYY-MM-DD)"},
                                "return_date": {"type": "string", "description": "Return date (YYYY-MM-DD, optional)"},
                                "trip_type": {"type": "string", "enum": ["one_way", "round_trip"], "default": "one_way"},
                                "max_results": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
                                "headless": {"type": "boolean", "default": True}
                            },
                            "required": ["origin", "destination", "departure_date"]
                        }
                    },
                    {
                        "name": "get_airport_info",
                        "description": "Get airport information and normalize queries",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Airport code or city name"}
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "get_scraper_status",
                        "description": "Check scraper health and configuration",
                        "inputSchema": {"type": "object", "properties": {}}
                    }
                ]
            })

        # Execute tool calls
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "search_flights":
                result = await search_flights_impl(**arguments)
                return create_success_response(request_id, {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                })

            elif tool_name == "get_airport_info":
                result = await get_airport_info_impl(**arguments)
                return create_success_response(request_id, {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                })

            elif tool_name == "get_scraper_status":
                result = await get_scraper_status_impl()
                return create_success_response(request_id, {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                })

            else:
                return create_error_response(request_id, -32601, f"Unknown tool: {tool_name}")

        else:
            return create_error_response(request_id, -32601, f"Unknown method: {method}")

    except Exception as e:
        return create_error_response(request_id, -32603, f"Internal error: {str(e)}")

async def main():
    """
    Main server loop for stdio mode.
    Reads JSON-RPC requests from stdin and writes responses to stdout.
    """
    while True:
        try:
            # Read line from stdin
            line = sys.stdin.readline()
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            # Remove BOM if present
            if line.startswith('\ufeff'):
                line = line[1:]

            # Parse JSON request
            try:
                request = json.loads(line)
            except json.JSONDecodeError as e:
                error_response = create_error_response(None, -32700, f"Parse error: {str(e)}")
                print(json.dumps(error_response), flush=True)
                continue

            # Handle request and send response
            response = await handle_request(request)
            
            if response is not None:
                print(json.dumps(response), flush=True)

        except EOFError:
            break
        except Exception:
            continue  # Keep server running on unexpected errors

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception:
        sys.exit(1)