# Google Flights MCP Server - Roo Integration Guide

## Overview

The Google Flights MCP Server has been successfully added to Roo's global MCP configuration. This allows you to use flight search capabilities directly through Roo's MCP interface.

## Configuration Details

The server has been configured in Roo's MCP settings at:
```
C:/Users/chons/AppData/Roaming/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json
```

**Server Name**: `google-flights`

**Configuration**:
```json
{
  "mcpServers": {
    "google-flights": {
      "command": "python",
      "args": [
        "c:/Users/chons/Documents/Dev/flight-scrapper-2/mcp_server_simple.py"
      ],
      "env": {
        "PYTHONPATH": "c:/Users/chons/Documents/Dev/flight-scrapper-2"
      }
    }
  }
}
```

## Available MCP Tools

Once the server is connected, you'll have access to these MCP tools:

### 1. `search_flights`
Search for flights between airports with comprehensive options.

**Parameters:**
- `origin` (string, required): Origin airport code or city name
- `destination` (string, required): Destination airport code or city name  
- `departure_date` (string, required): Departure date in YYYY-MM-DD format
- `return_date` (string, optional): Return date for round-trip flights
- `trip_type` (string, optional): "one_way" or "round_trip" (default: "one_way")
- `max_results` (integer, optional): Maximum results to return, 1-50 (default: 10)
- `headless` (boolean, optional): Run browser in headless mode (default: true)

### 2. `get_airport_info`
Get airport code information and normalize airport queries.

**Parameters:**
- `query` (string, required): Airport code or city name to look up

### 3. `get_scraper_status`
Check the health and configuration of the flight scraper.

**Parameters:** None

## Usage Instructions

1. **Restart Roo/VSCode** after adding the MCP server configuration to ensure it's loaded.

2. **Connect to the MCP Server** through Roo's interface - the server should appear as "google-flights".

3. **Use the Tools** through Roo's MCP tool interface:
   - Ask Roo to search for flights: "Search for flights from JFK to LAX on 2024-07-15"
   - Get airport information: "What airport code is used for New York?"
   - Check server status: "Check the status of the flight scraper"

## Supported Airport Codes

The server includes mappings for common cities:
- New York, NYC → JFK
- Los Angeles, LA → LAX  
- San Francisco, SF → SFO
- Chicago → ORD
- And many more...

## Troubleshooting

### Server Not Starting
1. Ensure all dependencies are installed:
   ```bash
   cd c:/Users/chons/Documents/Dev/flight-scrapper-2
   pip install -r requirements.txt
   ```

2. Install Playwright browsers:
   ```bash
   playwright install
   ```

### Connection Issues
1. Check if the server is running on port 8000
2. Ensure no firewall is blocking the connection
3. Restart Roo/VSCode to reload MCP configuration

### Server Status Check
You can manually test the server:
```bash
cd c:/Users/chons/Documents/Dev/flight-scrapper-2
python mcp_server_simple.py
```

## Manual Server Commands

- **Start stdio server**: `python mcp_server_simple.py`
- **Test with initialize**: `echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}' | python mcp_server_simple.py`
- **List tools**: `echo '{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}' | python mcp_server_simple.py`
- **Old HTTP server (if needed)**: `python run_mcp_server.py --debug`

## Security Notes

- The server is configured to run on localhost by default for security
- All flight searches are performed through automated browser sessions
- No personal data is stored or transmitted beyond search parameters

## Support

For issues with the MCP server implementation, check:
1. [`MCP_SERVER_GUIDE.md`](./MCP_SERVER_GUIDE.md) - Complete server documentation
2. [`README.md`](./README.md) - Project overview and setup
3. Server logs for detailed error information

---

**Status**: ✅ Successfully configured and ready to use
**Last Updated**: 2025-06-15