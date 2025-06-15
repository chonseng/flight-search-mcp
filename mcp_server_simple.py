#!/usr/bin/env python3
"""
Simple MCP Server for Google Flights Scraper - stdio mode only.
This version avoids asyncio event loop conflicts.
"""

import json
import sys
import asyncio
from datetime import datetime
from typing import Any, Dict

# Import our flight scraper components
from flight_scraper.core.scraper import scrape_flights_async
from flight_scraper.core.models import TripType
from flight_scraper.mcp.server import (
    search_flights_impl, 
    get_airport_info_impl, 
    get_scraper_status_impl,
    normalize_airport_input
)

def create_error_response(request_id: str, error_code: int, message: str) -> Dict[str, Any]:
    """Create an MCP error response."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": error_code,
            "message": message
        }
    }

def create_success_response(request_id: str, result: Any) -> Dict[str, Any]:
    """Create an MCP success response."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result
    }

async def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle an MCP request."""
    try:
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        if method == "initialize":
            return create_success_response(request_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "google-flights",
                    "version": "1.0.0"
                }
            })

        elif method == "notifications/initialized":
            # No response needed for notifications
            return None

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
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
            })

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "search_flights":
                result = await search_flights_impl(**arguments)
                return create_success_response(request_id, {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                })

            elif tool_name == "get_airport_info":
                result = await get_airport_info_impl(**arguments)
                return create_success_response(request_id, {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                })

            elif tool_name == "get_scraper_status":
                print(json.dumps({
                    "jsonrpc": "2.0",
                    "method": "notifications/message",
                    "params": {
                        "level": "debug",
                        "logger": "google-flights",
                        "data": "get_scraper_status called - starting execution"
                    }
                }), file=sys.stderr, flush=True)
                
                try:
                    result = await get_scraper_status_impl()
                    print(json.dumps({
                        "jsonrpc": "2.0",
                        "method": "notifications/message",
                        "params": {
                            "level": "debug",
                            "logger": "google-flights",
                            "data": f"get_scraper_status completed successfully: {result.get('success', 'unknown')}"
                        }
                    }), file=sys.stderr, flush=True)
                    
                    return create_success_response(request_id, {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    })
                except Exception as e:
                    print(json.dumps({
                        "jsonrpc": "2.0",
                        "method": "notifications/message",
                        "params": {
                            "level": "error",
                            "logger": "google-flights",
                            "data": f"get_scraper_status failed with error: {str(e)}"
                        }
                    }), file=sys.stderr, flush=True)
                    raise

            else:
                return create_error_response(request_id, -32601, f"Unknown tool: {tool_name}")

        else:
            return create_error_response(request_id, -32601, f"Unknown method: {method}")

    except Exception as e:
        return create_error_response(request_id, -32603, f"Internal error: {str(e)}")

async def main():
    """Main server loop."""
    print(json.dumps({
        "jsonrpc": "2.0",
        "method": "notifications/message",
        "params": {
            "level": "info",
            "logger": "google-flights",
            "data": "MCP Server starting in stdio mode"
        }
    }), file=sys.stderr, flush=True)
    
    # Add startup diagnostic
    print(json.dumps({
        "jsonrpc": "2.0",
        "method": "notifications/message",
        "params": {
            "level": "debug",
            "logger": "google-flights",
            "data": f"Server PID: {sys.argv}, Python path: {sys.path[0]}"
        }
    }), file=sys.stderr, flush=True)

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

            # Handle request
            response = await handle_request(request)
            
            # Send response (if any - notifications don't need responses)
            if response is not None:
                print(json.dumps(response), flush=True)

        except EOFError:
            break
        except Exception as e:
            print(json.dumps({
                "jsonrpc": "2.0",
                "method": "notifications/message",
                "params": {
                    "level": "error",
                    "logger": "google-flights",
                    "data": f"Server error: {str(e)}"
                }
            }), file=sys.stderr, flush=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(json.dumps({
            "jsonrpc": "2.0",
            "method": "notifications/message", 
            "params": {
                "level": "error",
                "logger": "google-flights",
                "data": f"Fatal error: {str(e)}"
            }
        }), file=sys.stderr, flush=True)
        sys.exit(1)