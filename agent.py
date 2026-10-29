"""
agent.py

The FitFindr planning loop. It parses a natural-language request, searches the
mock listing dataset, preserves state between tool calls, and stops early when a
step cannot produce useful input for the next tool.
"""

import re

from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """Initialize the state for one FitFindr interaction."""
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "adjustments": [],
        "error": None,
    }


# ── query parsing ─────────────────────────────────────────────────────────────

_PRICE_PATTERNS = [
    re.compile(
        r"\b(?:under|below|less\s+than|up\s+to|max(?:imum)?(?:\s+of)?)\s*\$?\s*(\d+(?:\.\d+)?)",
        re.IGNORECASE,
    ),
    re.compile(r"\$(\d+(?:\.\d+)?)\s*(?:max|maximum)\b", re.IGNORECASE),
]

_SIZE_PATTERN = re.compile(
    r"\b(?:in\s+)?size\s+((?:XXXL|XXL|XXS|XL|XS|[SML])|(?:W\d+(?:\s*L\d+)?)|(?:\d+(?:\.\d+)?))\b",
    re.IGNORECASE,
)


def _parse_query(query: str) -> dict:
    """Extract description, size, and max price using deterministic parsing."""
    original = (query or "").strip()
    working = original

    max_price = None
    for pattern in _PRICE_PATTERNS:
        match = pattern.search(working)
        if match:
            try:
                max_price = float(match.group(1))
            except (TypeError, ValueError):
                max_price = None
            working = pattern.sub(" ", working, count=1)
            break

    size = None
    size_match = _SIZE_PATTERN.search(working)
    if size_match:
        size = size_match.group(1).strip().upper()
        size = re.sub(r"\s+", " ", size)
        working = _SIZE_PATTERN.sub(" ", working, count=1)

    # Styling context often follows the first sentence. Search should focus on
    # the requested item rather than the user's existing wardrobe description.
    working = re.split(
        r"(?:[.!?]\s+|\bI\s+mostly\s+wear\b|\bI\s+usually\s+wear\b|\bhow\s+would\s+I\s+style\b|\bwhat'?s\s+out\s+there\b)",
        working,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    # Remove common request scaffolding while leaving fashion words intact.
    working = re.sub(
        r"^\s*(?:i(?:'m| am)?\s+looking\s+for|looking\s+for|find\s+me|i\s+want|"
        r"can\s+you\s+find(?:\s+me)?|show\s+me)\s+",
        "",
        working,
        flags=re.IGNORECASE,
    )
    working = re.sub(r"\b(?:please|something\s+like)\b", " ", working, flags=re.IGNORECASE)
    working = re.sub(r"\s+", " ", working).strip(" ,.-")

    description = working or original
    return {
        "description": description,
        "size": size,
        "max_price": max_price,
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """Run one complete FitFindr interaction and return its session state."""
    session = _new_session(query, wardrobe)

    if not isinstance(query, str) or not query.strip():
        session["error"] = "Please describe what you're looking for."
        return session

    parsed = _parse_query(query)
    session["parsed"] = parsed

    description = parsed["description"]
    size = parsed["size"]
    max_price = parsed["max_price"]

    # First attempt uses every constraint the user provided.
    results = search_listings(description, size=size, max_price=max_price)
    session["search_results"] = results

    # Stretch: retry once without size if that filter was too restrictive.
    if not results and size is not None:
        results = search_listings(description, size=None, max_price=max_price)
        session["search_results"] = results
        session["adjustments"].append(
            f"No exact matches in size {size}, so I retried without the size filter."
        )

    # If still empty, make one final retry without the budget ceiling.
    if not results and max_price is not None:
        results = search_listings(description, size=None, max_price=None)
        session["search_results"] = results
        session["adjustments"].append(
            f"I also retried without the ${max_price:g} price ceiling."
        )

    if not results:
        session["error"] = (
            "I couldn't find a matching listing even after loosening the size and price filters. "
            "Try a broader item description, another size, or a higher budget."
        )
        return session

    # State produced by search flows directly to the next tool.
    session["selected_item"] = results[0]

    outfit = suggest_outfit(session["selected_item"], session["wardrobe"])
    session["outfit_suggestion"] = outfit

    if not isinstance(outfit, str) or not outfit.strip():
        session["error"] = (
            "I found a listing, but I couldn't generate a usable outfit suggestion. "
            "Try again or add more wardrobe details."
        )
        return session

    session["fit_card"] = create_fit_card(
        session["outfit_suggestion"],
        session["selected_item"],
    )
    return session


# ── CLI smoke tests ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Parsed: {session['parsed']}")
        print(f"Found: {session['selected_item']['title']}")
        if session["adjustments"]:
            print("Adjustments:", " ".join(session["adjustments"]))
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Parsed: {session2['parsed']}")
    print(f"Adjustments: {session2['adjustments']}")
    print(f"Error message: {session2['error']}")
