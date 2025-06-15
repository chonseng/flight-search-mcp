#!/usr/bin/env python3
"""
MCP Server startup script for Google Flights Scraper.

This script provides an easy way to start the MCP server with proper
configuration and error handling.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from flight_scraper.mcp.server import run_server
    from flight_scraper.utils import setup_logging
    from loguru import logger
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you have installed all dependencies with: pip install -r requirements.txt")
    sys.exit(1)


def main():
    """Main function to start the MCP server."""
    parser = argparse.ArgumentParser(
        description="Google Flights MCP Server - Expose flight scraping capabilities via MCP protocol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_mcp_server.py                     # Start server on localhost:8000
  python run_mcp_server.py --port 8080         # Start server on port 8080
  python run_mcp_server.py --host 0.0.0.0      # Allow external connections
  python run_mcp_server.py --debug             # Enable debug logging

Available MCP Tools:
  - search_flights: Search for flights between airports
  - get_airport_info: Get airport code information
  - get_scraper_status: Check scraper health and configuration
        """
    )
    
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host to bind the server to (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)"
    )
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Run in stdio mode for MCP clients (default for Roo integration)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--log-file",
        help="Log file path (default: flight_scraper.log)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    try:
        if args.debug:
            # Override default logging for debug mode
            logger.remove()
            logger.add(
                sys.stdout,
                level="DEBUG",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
                colorize=True
            )
            if args.log_file:
                logger.add(
                    args.log_file,
                    level="DEBUG",
                    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
                    rotation="10 MB",
                    retention="7 days"
                )
        else:
            setup_logging()
            if args.log_file:
                logger.add(
                    args.log_file,
                    level="INFO",
                    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
                    rotation="10 MB",
                    retention="7 days"
                )
    except Exception as e:
        print(f"Error setting up logging: {e}")
        sys.exit(1)
    
    # Display startup information
    logger.info("=" * 60)
    logger.info("Google Flights MCP Server")
    logger.info("=" * 60)
    logger.info(f"Server Host: {args.host}")
    logger.info(f"Server Port: {args.port}")
    logger.info(f"Debug Mode: {args.debug}")
    if args.log_file:
        logger.info(f"Log File: {args.log_file}")
    logger.info("=" * 60)
    
    # Check dependencies
    try:
        import playwright
        import fastmcp
        import pydantic
        logger.info("✅ All required dependencies are available")
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.error("Please install requirements: pip install -r requirements.txt")
        sys.exit(1)
    
    # Verify Playwright browsers are installed
    try:
        from playwright.async_api import async_playwright
        logger.info("✅ Playwright is available")
    except Exception as e:
        logger.warning(f"⚠️  Playwright issue: {e}")
        logger.warning("You may need to install Playwright browsers: playwright install")
    
    # Start the server
    try:
        if args.stdio:
            logger.info("🚀 Starting MCP server in stdio mode...")
            logger.info("Server will communicate via stdin/stdout")
            asyncio.run(run_server(use_stdio=True))
        else:
            logger.info("🚀 Starting MCP server in HTTP mode...")
            logger.info(f"Server will run on {args.host}:{args.port}")
            logger.info("Press Ctrl+C to stop the server")
            asyncio.run(run_server(host=args.host, port=args.port))
            
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server failed to start: {str(e)}")
        if args.debug:
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()