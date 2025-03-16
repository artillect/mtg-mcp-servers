# MTG Deck Manager MCP Servers

This project provides Model Context Protocol (MCP) servers for interacting with Magic: The Gathering decks and card information directly through Claude.

## Features

- **MTG Deck Manager**: Upload decks, draw cards, manage your hand, perform mulligans, and handle sideboarding
- **Scryfall API Integration**: Search for cards, get random cards, and look up card information

## Installation

1. Clone this repository to your local machine:
```bash
git clone https://github.com/artillect/mtg-deck-mcp-server.git
cd mtg-deck-mcp-server
```

2. Set up a Python virtual environment:
```bash
# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install fastmcp httpx
```

## Claude Desktop Client Configuration

Add the following to your Claude config:

```json
{
    "mcp_servers": {
        "mtg-server": {
            "command": "C:\\Path\\To\\Your\\Project\\.venv\\Scripts\\python.exe",
            "args": [
                "C:\\Path\\To\\Your\\Project\\mtg_server.py"
            ]
        },
        "scryfall": {
            "command": "C:\\Path\\To\\Your\\Project\\.venv\\Scripts\\python.exe",
            "args": [
                "C:\\Path\\To\\Your\\Project\\scryfall_server.py"
            ]
        }
    }
}
```

Make sure to adjust the paths to match your local installation.

## Usage

After setting up the servers in your Claude client, you can interact with them by asking Claude to:

- Upload an MTG deck list
- Draw cards from your deck
- View your hand
- Search for card information via Scryfall
- Get random cards or search by name

## Notes

- The Scryfall server may occasionally crash due to ongoing development.
- Make sure both servers are running when you want to use their respective features. 
