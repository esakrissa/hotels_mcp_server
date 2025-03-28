import json
import httpx
import logging
import signal
import sys
import argparse
from typing import Dict, List, Any, Optional
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("hotels-mcp-server")

# Initialize FastMCP server
mcp = FastMCP("hotels")

# Constants
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "booking-com15.p.rapidapi.com")

# Validate required environment variables
if not RAPIDAPI_KEY:
    logger.error("RAPIDAPI_KEY environment variable is not set. Please create a .env file with your API key.")
    sys.exit(1)

async def make_rapidapi_request(endpoint: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Make a request to the RapidAPI with proper error handling."""
    url = f"https://{RAPIDAPI_HOST}{endpoint}"
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }
    
    logger.info(f"Making API request to {endpoint} with params: {params}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            logger.info(f"API request to {endpoint} successful")
            return response.json()
        except Exception as e:
            logger.error(f"API request to {endpoint} failed: {str(e)}")
            return {"error": str(e)}

@mcp.tool()
async def search_destinations(query: str) -> str:
    """Search for hotel destinations by name.
    
    Args:
        query: The destination to search for (e.g., "Paris", "New York", "Tokyo")
    """
    logger.info(f"Searching for destinations with query: {query}")
    endpoint = "/api/v1/hotels/searchDestination"
    params = {"query": query}
    
    result = await make_rapidapi_request(endpoint, params)
    
    if "error" in result:
        logger.error(f"Error in search_destinations: {result['error']}")
        return f"Error fetching destinations: {result['error']}"
    
    # Format the response
    formatted_results = []
    
    if "data" in result and isinstance(result["data"], list):
        destinations_count = len(result["data"])
        logger.info(f"Found {destinations_count} destinations for query: {query}")
        for destination in result["data"]:
            dest_info = (
                f"Name: {destination.get('name', 'Unknown')}\n"
                f"Type: {destination.get('dest_type', 'Unknown')}\n"
                f"City ID: {destination.get('city_ufi', 'N/A')}\n"
                f"Region: {destination.get('region', 'Unknown')}\n"
                f"Country: {destination.get('country', 'Unknown')}\n"
                f"Coordinates: {destination.get('latitude', 'N/A')}, {destination.get('longitude', 'N/A')}\n"
            )
            formatted_results.append(dest_info)
        
        return "\n---\n".join(formatted_results) if formatted_results else "No destinations found matching your query."
    else:
        logger.warning(f"Unexpected response format from API for query: {query}")
        return "Unexpected response format from the API."

@mcp.tool()
async def get_hotels(destination_id: str, checkin_date: str, checkout_date: str, adults: int = 2) -> str:
    """Get hotels for a specific destination.
    
    Args:
        destination_id: The destination ID (city_ufi from search_destinations)
        checkin_date: Check-in date in YYYY-MM-DD format
        checkout_date: Check-out date in YYYY-MM-DD format
        adults: Number of adults (default: 2)
    """
    logger.info(f"Getting hotels for destination_id: {destination_id}, checkin: {checkin_date}, checkout: {checkout_date}, adults: {adults}")
    endpoint = "/api/v1/hotels/searchHotels"
    params = {
        "dest_id": destination_id,
        "search_type": "CITY",
        "arrival_date": checkin_date,
        "departure_date": checkout_date,
        "adults": str(adults)
    }
    
    result = await make_rapidapi_request(endpoint, params)
    
    if "error" in result:
        logger.error(f"Error in get_hotels: {result['error']}")
        return f"Error fetching hotels: {result['error']}"
    
    # Format the response
    formatted_results = []
    
    if "data" in result and "hotels" in result["data"] and isinstance(result["data"]["hotels"], list):
        hotels_count = len(result["data"]["hotels"])
        logger.info(f"Found {hotels_count} hotels for destination: {destination_id}")
        hotels = result["data"]["hotels"]
        for hotel_entry in hotels[:10]:  # Limit to 10 hotels to avoid too much text
            if "property" in hotel_entry:
                property_data = hotel_entry["property"]
                
                # Parse accessibility label for room info
                room_info = "Not available"
                accessibility_label = hotel_entry.get("accessibilityLabel", "")
                if accessibility_label:
                    # Try to extract room type information
                    import re
                    room_match = re.search(r'(Hotel room|Entire villa|Private suite|Private room)[^\.]*', accessibility_label)
                    if room_match:
                        room_info = room_match.group(0).strip()
                
                hotel_info = (
                    f"Name: {property_data.get('name', 'Unknown')}\n"
                    f"Location: {property_data.get('wishlistName', 'Unknown')}\n"
                    f"Rating: {property_data.get('reviewScore', 'N/A')}/10\n"
                    f"Reviews: {property_data.get('reviewCount', 'N/A')} ({property_data.get('reviewScoreWord', 'N/A')})\n"
                )
                
                # Add room information
                hotel_info += f"Room: {room_info}\n"
                
                # Add pricing info if available
                if "priceBreakdown" in property_data and "grossPrice" in property_data["priceBreakdown"]:
                    price_data = property_data["priceBreakdown"]["grossPrice"]
                    hotel_info += f"Price: {price_data.get('currency', '$')}{price_data.get('value', 'N/A')}\n"
                    
                    # Add discount information if available
                    if "strikethroughPrice" in property_data["priceBreakdown"]:
                        original_price = property_data["priceBreakdown"]["strikethroughPrice"].get("value", "N/A")
                        if original_price != "N/A":
                            discount_pct = 0
                            try:
                                current = float(price_data.get('value', 0))
                                original = float(original_price)
                                if original > 0:
                                    discount_pct = round((1 - current/original) * 100)
                            except (ValueError, TypeError):
                                pass
                            
                            if discount_pct > 0:
                                hotel_info += f"Discount: {discount_pct}% off original price\n"
                else:
                    hotel_info += "Price: Not available\n"
                
                # Add location coordinates
                if "latitude" in property_data and "longitude" in property_data:
                    hotel_info += f"Coordinates: {property_data.get('latitude', 'N/A')}, {property_data.get('longitude', 'N/A')}\n"
                
                # Add star rating
                if "propertyClass" in property_data:
                    stars = property_data.get('propertyClass', 'N/A')
                    hotel_info += f"Stars: {stars}\n"
                
                # Add photo URL
                if property_data.get('photoUrls') and len(property_data.get('photoUrls', [])) > 0:
                    hotel_info += f"Photo: {property_data['photoUrls'][0]}\n"
                
                # Add check-in/check-out times
                checkin = property_data.get('checkin', {})
                checkout = property_data.get('checkout', {})
                if checkin and checkout:
                    hotel_info += f"Check-in: {checkin.get('fromTime', 'N/A')}-{checkin.get('untilTime', 'N/A')}\n"
                    hotel_info += f"Check-out: by {checkout.get('untilTime', 'N/A')}\n"
                
                formatted_results.append(hotel_info)
            else:
                formatted_results.append("Hotel information not available in the expected format.")
        
        return "\n---\n".join(formatted_results) if formatted_results else "No hotels found for this destination and dates."
    else:
        logger.warning(f"Unexpected response format from API for destination: {destination_id}")
        return "Unexpected response format from the API."

def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Received shutdown signal, shutting down gracefully...")
    sys.exit(0)

def main():
    """Main function to run the Hotels MCP server."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Hotels MCP Server')
    args = parser.parse_args()
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    try:
        # Use STDIO transport - it's the most reliable for Claude for Desktop
        logger.info("Starting Hotels MCP Server with stdio transport...")
        mcp.run(transport='stdio')
        return 0
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        return 1
    finally:
        logger.info("Hotels MCP Server shutting down...")

if __name__ == "__main__":
    sys.exit(main()) 