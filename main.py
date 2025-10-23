"""
Main entry point for the Google Flights scraper package.
Provides access to both CLI and MCP server functionality.
"""

import sys
import argparse


def main():
    """Main entry point with mode selection."""
    parser = argparse.ArgumentParser(
        description="Google Flights Scraper - CLI and MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="mode", help="Available modes")

    # CLI mode
    cli_parser = subparsers.add_parser("cli", help="Run CLI interface")

    # MCP server mode
    mcp_parser = subparsers.add_parser("mcp", help="Run MCP server")
    mcp_parser.add_argument("--stdio", action="store_true", help="Use stdio mode")
    mcp_parser.add_argument("--host", default="localhost", help="Host to bind to")
    mcp_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    mcp_parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args, remaining_args = parser.parse_known_args()

    if args.mode == "cli":
        from flight_scraper.cli.main import app

        # Forward remaining arguments to Typer by modifying sys.argv
        import sys

        original_argv = sys.argv
        sys.argv = ["cli"] + remaining_args
        app()
        sys.argv = original_argv
    elif args.mode == "mcp":
        import asyncio
        from flight_scraper.mcp.server import run_server
        from loguru import logger

        if args.debug:
            logger.remove()
            logger.add(lambda msg: print(msg, end=""), level="DEBUG")

        try:
            asyncio.run(run_server(host=args.host, port=args.port, use_stdio=args.stdio))
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
