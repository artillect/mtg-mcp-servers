from typing import Any, Optional
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("scryfall")

# Constants
API_BASE = "https://api.scryfall.com"
USER_AGENT = "ScryFallMCPServer/1.0"

async def make_scryfall_request(url: str) -> dict[str, Any] | None:
    """Make a request to the Scryfall API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

def format_card_info(card: dict[str, Any]) -> str:
    """Format a card object into a readable string."""
    info = [
        f"Name: {card.get('name', 'Unknown')}",
        f"Mana Cost: {card.get('mana_cost', 'Unknown')}",
        f"Type: {card.get('type_line', 'Unknown')}"
    ]
    
    if oracle_text := card.get('oracle_text'):
        info.append(f"Text: {oracle_text}")
    
    if power := card.get('power'):
        toughness = card.get('toughness')
        info.append(f"Power/Toughness: {power}/{toughness}")
    
    if loyalty := card.get('loyalty'):
        info.append(f"Loyalty: {loyalty}")
        
    if price := card.get('prices', {}).get('usd'):
        info.append(f"Price (USD): ${price}")
        
    if legalities := card.get('legalities'):
        legal_formats = [fmt for fmt, status in legalities.items() if status == 'legal']
        if legal_formats:
            info.append(f"Legal in: {', '.join(legal_formats)}")
    
    return "\n".join(info)

@mcp.tool()
async def search_cards(query: str) -> str:
    """Search for Magic cards using a Scryfall query.
    
    Args:
        query: A search query using Scryfall's syntax
    """
    url = f"{API_BASE}/cards/search?q={httpx.QueryParams({'q': query})}"
    data = await make_scryfall_request(url)
    
    if not data or "error" in data:
        return f"Error searching cards: {data.get('error', 'Unknown error')}"
    
    cards = data.get("data", [])
    if not cards:
        return "No cards found matching that query."
    
    results = []
    for card in cards[:5]:  # Limit to first 5 cards
        results.append(format_card_info(card))
        results.append("-" * 40)
    
    total_cards = data.get("total_cards", len(cards))
    if total_cards > 5:
        results.append(f"\nShowing 5 of {total_cards} total matches.")
    
    return "\n".join(results)

@mcp.tool()
async def get_random_card(query: Optional[str] = None) -> str:
    """Get a random Magic card, optionally filtered by a query.
    
    Args:
        query: Optional query to filter the random selection
    """
    url = f"{API_BASE}/cards/random"
    if query:
        url = f"{url}?q={httpx.QueryParams({'q': query})}"
    
    data = await make_scryfall_request(url)
    
    if not data or "error" in data:
        return f"Error fetching random card: {data.get('error', 'Unknown error')}"
    
    return format_card_info(data)

@mcp.tool()
async def get_card_by_name(name: str, fuzzy: bool = True) -> str:
    """Get a specific card by name.
    
    Args:
        name: The name of the card to search for
        fuzzy: Whether to use fuzzy name matching (default: True)
    """
    search_type = "fuzzy" if fuzzy else "exact"
    url = f"{API_BASE}/cards/named?{search_type}={httpx.QueryParams({search_type: name})}"
    
    data = await make_scryfall_request(url)
    
    if not data or "error" in data:
        return f"Error finding card: {data.get('error', 'Unknown error')}"
    
    return format_card_info(data)

if __name__ == "__main__":
    mcp.run()