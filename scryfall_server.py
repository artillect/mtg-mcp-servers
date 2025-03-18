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
async def search_cards(query: str, page_size: int = 5, page: int = 1) -> str:
    """Search for Magic cards using a Scryfall query.
    
    Args:
        query: A search query using Scryfall's syntax
        page_size: Number of cards to display per page (default: 5)
        page: Which page of results to display (default: 1)
    """
    # Construct the URL with proper URL encoding
    params = httpx.QueryParams({'q': query})
    base_url = f"{API_BASE}/cards/search?{params}"
    
    # If not the first page, we need to navigate through pages
    current_page = 1
    data = await make_scryfall_request(base_url)
    
    # Handle error or no results
    if not data or "error" in data:
        return f"Error searching cards: {data.get('error', 'Unknown error')}"
    
    # Navigate to requested page if needed
    while current_page < page and data.get("has_more", False):
        current_page += 1
        next_page_url = data.get("next_page")
        if not next_page_url:
            return f"Could not navigate to page {page}. Only {current_page-1} pages available."
        
        data = await make_scryfall_request(next_page_url)
        if not data or "error" in data:
            return f"Error retrieving page {current_page}: {data.get('error', 'Unknown error')}"
    
    cards = data.get("data", [])
    if not cards:
        return "No cards found matching that query."
    
    results = []
    # Only display the requested number of cards per page
    display_cards = cards[:page_size]
    
    for card in display_cards:
        results.append(format_card_info(card))
        results.append("-" * 40)
    
    # Add pagination information
    total_cards = data.get("total_cards", len(cards))
    start_idx = (page - 1) * page_size + 1
    end_idx = start_idx + len(display_cards) - 1
    
    pagination_info = [
        f"\nShowing cards {start_idx}-{end_idx} of {total_cards} total matches.",
    ]
    
    if page > 1:
        pagination_info.append(f"Currently on page {page}.")
    
    if data.get("has_more", False):
        pagination_info.append(f"More results available. Use page={page+1} to see the next page.")
    
    results.append("\n".join(pagination_info))
    
    return "\n".join(results)

@mcp.tool()
async def get_random_card(query: Optional[str] = None) -> str:
    """Get a random Magic card, optionally filtered by a query.
    
    Args:
        query: Optional query to filter the random selection
    """
    url = f"{API_BASE}/cards/random"
    if query:
        url = f"{url}?q={query}"
    
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
    url = f"{API_BASE}/cards/named?{search_type}={name}"
    
    data = await make_scryfall_request(url)
    
    if not data or "error" in data:
        return f"Error finding card: {data.get('error', 'Unknown error')}"
    
    return format_card_info(data)

if __name__ == "__main__":
    mcp.run()