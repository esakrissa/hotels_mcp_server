#!/usr/bin/env python3

"""
Hotels MCP Server - Entry point
"""

import sys
print("Importing from hotels_mcp.hotels_server...")
from hotels_mcp.hotels_server import main
print("Import successful!")

if __name__ == "__main__":
    print("Starting main function...")
    sys.exit(main()) 