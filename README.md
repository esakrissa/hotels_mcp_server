# Hotels MCP Server

A Model Context Protocol (MCP) server that allows LLMs to search for hotels and destinations using the Booking.com API.

## Features

- Search for destinations by name
- Get hotel listings for specific destinations with dates
- Rich hotel information including:
  - Room details and types
  - Pricing and discounts
  - Ratings and reviews
  - Photos
  - Check-in/check-out times
  - Star ratings

## API Integration

This MCP server uses the [Booking.com API](https://rapidapi.com/apidojo/api/booking-com/) via RapidAPI. You'll need:

1. A RapidAPI account
2. Subscribe to the Booking.com API
3. Get your API key

The current implementation uses two endpoints:
- `/api/v1/hotels/searchDestination`: Search for destinations
- `/api/v1/hotels/searchHotels`: Get hotels for a destination

## Setup and Installation

### Prerequisites

- Python 3.11+
- MCP SDK (`pip install mcp`)
- httpx (`pip install httpx`)
- python-dotenv (`pip install python-dotenv`)

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/username/hotels_mcp_server.git
   cd hotels_mcp_server
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your RapidAPI credentials:
   - Copy `.env.example` to `.env`
   - Add your RapidAPI key from [Booking.com API on RapidAPI](https://rapidapi.com/tipsters/api/booking-com) to the `.env` file

### Running the Server

Run the server with:

```bash
python main.py
```

The server uses stdio transport by default for compatibility with MCP clients like Cursor.

## Using with MCP Clients

### Cursor

1. Edit `~/.cursor/mcp.json`:
   ```json
   {
     "hotels": {
       "command": "python",
       "args": [
         "/path/to/hotels_mcp_server/main.py"
       ]
     }
   }
   ```

2. Restart Cursor

3. Use natural language to search for hotels in Cursor:
   - "Find hotels in Paris for next week"
   - "What are the best-rated hotels in Tokyo?"

### MCP Inspector

Test your server with MCP Inspector:

```bash
npx @modelcontextprotocol/inspector python main.py
```

This opens an interactive UI where you can:
- View available tools
- Send test requests
- See server responses

## Available Tools

1. `search_destinations`: Search for destinations by name
   - Parameter: `query` - Destination name (e.g., "Paris", "New York")

2. `get_hotels`: Get hotels for a destination
   - Parameters:
     - `destination_id`: Destination ID from search_destinations
     - `checkin_date`: Check-in date (YYYY-MM-DD)
     - `checkout_date`: Check-out date (YYYY-MM-DD)
     - `adults`: Number of adults (default: 2)

## Code Structure

- `main.py`: The entry point for the server
- `hotels_mcp/`: The core MCP implementation
  - `__init__.py`: Package initialization
  - `hotels_server.py`: MCP server implementation with tool definitions

## License

MIT © Esa Krissa 2025