from mcp.server.fastmcp import FastMCP
import random
from typing import List, Dict, Any, Optional

# Initialize FastMCP server
mcp = FastMCP("mtg-manager")

# State management
state = {
    "deck": [],
    "sideboard": [],
    "hand": []
}

# Helper functions
def parse_deck_list(deck_text: str) -> Dict[str, List[Dict[str, Any]]]:
    """Parse a deck list into main deck and sideboard card objects."""
    main_deck = []
    sideboard = []
    
    lines = deck_text.strip().split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for section headers
        if line.lower() == "deck":
            current_section = "main"
            continue
        elif line.lower() == "sideboard":
            current_section = "side"
            continue
        
        # Skip if no section defined yet
        if current_section is None:
            continue
        
        # Try to parse card entry (number + name)
        parts = line.split(' ', 1)
        if len(parts) != 2:
            continue
            
        try:
            count = int(parts[0])
            card_name = parts[1]
            
            # Create card objects
            for i in range(count):
                card = {
                    "name": card_name,
                    "id": f"{card_name.lower().replace(' ', '_')}_{len(main_deck) + len(sideboard) + i}"
                }
                
                if current_section == "main":
                    main_deck.append(card)
                else:  # sideboard
                    sideboard.append(card)
                    
        except ValueError:
            # Skip lines that don't start with a number
            continue
    
    return {
        "main_deck": main_deck,
        "sideboard": sideboard
    }

@mcp.tool()
async def upload_deck(deck_list: str) -> str:
    """Upload a Magic: The Gathering deck list.
    
    Args:
        deck_list: Text format deck list with "Deck" and "Sideboard" sections
    """
    parsed_cards = parse_deck_list(deck_list)
    main_deck = parsed_cards["main_deck"]
    sideboard = parsed_cards["sideboard"]
    
    state["deck"] = main_deck
    state["sideboard"] = sideboard
    state["hand"] = []
    
    random.shuffle(state["deck"])
    
    return f"Deck uploaded with {len(state['deck'])} main deck cards and {len(state['sideboard'])} sideboard cards."

@mcp.tool()
async def draw_card(count: int = 1) -> str:
    """Draw cards from your deck to your hand.
    
    Args:
        count: Number of cards to draw (default: 1)
    """
    if len(state["deck"]) < count:
        return f"Not enough cards in deck. Only {len(state['deck'])} remaining."
    
    drawn_cards = []
    for _ in range(count):
        card = state["deck"].pop(0)
        state["hand"].append(card)
        drawn_cards.append(card["name"])
    
    return f"Drew {count} card(s): {', '.join(drawn_cards)}"

@mcp.tool()
async def play_card(card_name: str) -> str:
    """Play a card from your hand to the battlefield/stack.
    
    Args:
        card_name: Name of the card to play
    """
    for i, card in enumerate(state["hand"]):
        if card["name"].lower() == card_name.lower():
            played_card = state["hand"].pop(i)
            return f"Played {played_card['name']}."
    
    return f"Card '{card_name}' not found in hand."

@mcp.tool()
async def view_hand() -> str:
    """View the cards in your hand."""
    if not state["hand"]:
        return "Your hand is empty."
    
    card_counts = {}
    for card in state["hand"]:
        name = card["name"]
        card_counts[name] = card_counts.get(name, 0) + 1
    
    hand_str = "\n".join([f"{count}x {name}" for name, count in card_counts.items()])
    return f"Your hand ({len(state['hand'])} cards):\n{hand_str}"

@mcp.tool()
async def view_deck_stats() -> str:
    """View statistics about your current deck."""
    if not state["deck"]:
        return "Your deck is empty."
    
    card_counts = {}
    for card in state["deck"]:
        name = card["name"]
        card_counts[name] = card_counts.get(name, 0) + 1
    
    result = [
        f"Cards in deck: {len(state['deck'])}",
        f"Cards in hand: {len(state['hand'])}",
        f"Sideboard cards: {len(state['sideboard'])}",
        "",
        "Top card types in deck:"
    ]
    
    # Sort by quantity
    sorted_cards = sorted(card_counts.items(), key=lambda x: x[1], reverse=True)
    for name, count in sorted_cards[:5]:  # Show top 5 cards
        result.append(f"  {count}x {name}")
    
    return "\n".join(result)

@mcp.tool()
async def mulligan(new_hand_size: Optional[int] = None) -> str:
    """Perform a mulligan, shuffling your hand into your deck and drawing a new hand.
    
    Args:
        new_hand_size: Number of cards to draw for new hand (default: same as current hand)
    """
    if not state["hand"]:
        return "Cannot mulligan with an empty hand."
    
    current_hand_size = len(state["hand"])
    draw_size = new_hand_size if new_hand_size is not None else current_hand_size
    
    # Return hand to deck
    state["deck"].extend(state["hand"])
    state["hand"] = []
    
    # Shuffle
    random.shuffle(state["deck"])
    
    # Draw new hand
    drawn_cards = []
    for _ in range(min(draw_size, len(state["deck"]))):
        card = state["deck"].pop(0)
        state["hand"].append(card)
        drawn_cards.append(card["name"])
    
    return f"Mulliganed and drew {len(drawn_cards)} new cards."

@mcp.tool()
async def sideboard_swap(remove_card: str, add_card: str) -> str:
    """Swap a card from your deck with a card from your sideboard.
    
    Args:
        remove_card: Name of card to remove from deck
        add_card: Name of card to add from sideboard
    """
    # Find card in sideboard
    sideboard_card_idx = None
    for i, card in enumerate(state["sideboard"]):
        if card["name"].lower() == add_card.lower():
            sideboard_card_idx = i
            break
    
    if sideboard_card_idx is None:
        return f"Card '{add_card}' not found in sideboard."
    
    # Find all instances of the card to remove (combine deck and hand)
    all_deck = state["deck"] + state["hand"]
    main_deck_card_indices = [
        i for i, card in enumerate(all_deck) 
        if card["name"].lower() == remove_card.lower()
    ]
    
    if not main_deck_card_indices:
        return f"Card '{remove_card}' not found in deck or hand."
    
    # Get the first instance and swap
    main_card_idx = main_deck_card_indices[0]  # Fixed variable name here
    main_card = all_deck.pop(main_card_idx)
    sideboard_card = state["sideboard"].pop(sideboard_card_idx)
    
    # Add removed card to sideboard
    state["sideboard"].append(main_card)
    
    # Rebuild deck and hand
    if main_card_idx < len(state["deck"]):
        # Was in deck
        state["deck"].insert(main_card_idx, sideboard_card)
    else:
        # Was in hand
        hand_idx = main_card_idx - len(state["deck"])
        state["hand"].insert(hand_idx, sideboard_card)
    
    return f"Swapped out {main_card['name']} for {sideboard_card['name']} from sideboard."
@mcp.tool()
async def reset_game() -> str:
    """Reset the game state completely."""
    # Get all cards back including those in hand
    deck_backup = state["deck"].copy() + state["hand"].copy()
    state["deck"] = deck_backup
    state["hand"] = []
    
    random.shuffle(state["deck"])
    
    return "Game reset. Deck shuffled."

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')