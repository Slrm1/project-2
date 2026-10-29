"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Tools:
    search_listings(description, size, max_price)  -> list[dict]
    suggest_outfit(new_item, wardrobe)             -> str
    create_fit_card(outfit, new_item)              -> str
"""

import os
import re
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()

MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"


# ── Groq helpers ──────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


def _call_groq(prompt: str, temperature: float = 0.6) -> str:
    """Send one prompt to Groq and return stripped text.

    Kept as a small helper so tests can monkeypatch the network-dependent part.
    """
    client = _get_groq_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are FitFindr, a concise secondhand-fashion styling assistant. "
                    "Give practical, specific advice and do not invent wardrobe pieces."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=450,
    )
    return (response.choices[0].message.content or "").strip()


# ── Search helpers ────────────────────────────────────────────────────────────

_STOP_WORDS = {
    "a", "an", "and", "are", "for", "from", "i", "im", "i'm", "in", "is",
    "it", "looking", "me", "my", "of", "on", "or", "please", "some", "that",
    "the", "to", "want", "with", "would", "under", "below", "size", "find",
    "something", "out", "there", "how", "style", "wear", "mostly", "what",
}


def _tokens(text: str) -> set[str]:
    """Normalize text into meaningful lowercase search tokens."""
    return {
        token
        for token in re.findall(r"[a-z0-9]+", (text or "").lower())
        if token not in _STOP_WORDS and len(token) > 1
    }


def _listing_text(listing: dict) -> str:
    """Flatten the searchable fields of a listing into one string."""
    parts: list[str] = [
        str(listing.get("title", "")),
        str(listing.get("description", "")),
        str(listing.get("category", "")),
        str(listing.get("size", "")),
        str(listing.get("condition", "")),
        str(listing.get("brand") or ""),
        str(listing.get("platform", "")),
    ]
    parts.extend(str(x) for x in listing.get("style_tags", []))
    parts.extend(str(x) for x in listing.get("colors", []))
    return " ".join(parts).lower()


def _size_matches(requested_size: str | None, listing_size: str) -> bool:
    """Return whether a listing size satisfies a simple user size filter."""
    if not requested_size:
        return True

    requested = requested_size.strip().upper()
    available = (listing_size or "").strip().upper()

    if requested in {"XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"}:
        size_tokens = set(re.findall(r"XXXL|XXL|XXS|XL|XS|[SML]", available))
        return requested in size_tokens

    # Numeric sizes: size 8 should match "US 8" but not "US 8.5".
    if re.fullmatch(r"\d+(?:\.\d+)?", requested):
        return bool(re.search(rf"(?<![\d.]){re.escape(requested)}(?![\d.])", available))

    # Waist/length and other structured sizes such as W30 or M/L.
    return requested in available


# ── Tool 1: search_listings ──────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """Search the mock listings dataset and return relevant listings.

    Results are filtered by optional price and size constraints, then ranked by
    keyword overlap. The original listing dictionaries are returned so their
    structure remains compatible with the rest of the starter project.
    """
    try:
        listings = load_listings()
    except (OSError, ValueError, TypeError):
        return []

    query_tokens = _tokens(description)
    if not query_tokens:
        return []

    scored: list[tuple[int, float, dict]] = []

    for listing in listings:
        try:
            price = float(listing.get("price", 0))
        except (TypeError, ValueError):
            continue

        if max_price is not None and price > float(max_price):
            continue

        if not _size_matches(size, str(listing.get("size", ""))):
            continue

        title_tokens = _tokens(str(listing.get("title", "")))
        tag_tokens = _tokens(" ".join(str(x) for x in listing.get("style_tags", [])))
        all_tokens = _tokens(_listing_text(listing))

        # Title matches matter most, then explicit style tags, then other fields.
        title_overlap = len(query_tokens & title_tokens)
        tag_overlap = len(query_tokens & tag_tokens)
        general_overlap = len(query_tokens & all_tokens)
        score = (title_overlap * 4) + (tag_overlap * 3) + general_overlap

        if score > 0:
            # Lower prices break relevance ties in a user-friendly way.
            scored.append((score, -price, listing))

    scored.sort(key=lambda row: (row[0], row[1]), reverse=True)
    return [listing for _, _, listing in scored]


# ── Tool 2: suggest_outfit ───────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """Suggest 1–2 outfits using the new item and the user's wardrobe."""
    if not isinstance(new_item, dict) or not new_item.get("title"):
        return "I couldn't suggest an outfit because the selected listing is missing item details."

    wardrobe_items = []
    if isinstance(wardrobe, dict):
        wardrobe_items = wardrobe.get("items") or []

    item_summary = (
        f"New thrift item: {new_item.get('title')} | "
        f"category: {new_item.get('category')} | size: {new_item.get('size')} | "
        f"colors: {', '.join(new_item.get('colors', []))} | "
        f"style tags: {', '.join(new_item.get('style_tags', []))}."
    )

    if wardrobe_items:
        formatted_items = []
        for item in wardrobe_items:
            notes = item.get("notes") or "no extra notes"
            formatted_items.append(
                f"- {item.get('name')} ({item.get('category')}); "
                f"colors: {', '.join(item.get('colors', []))}; "
                f"style: {', '.join(item.get('style_tags', []))}; notes: {notes}"
            )

        prompt = f"""
{item_summary}

The user's wardrobe contains:
{chr(10).join(formatted_items)}

Suggest 1 or 2 complete outfits built around the thrift item. Use the exact names
of real wardrobe pieces above whenever possible. Explain why the pieces work
together and include one small styling detail such as layering, cuffing, tucking,
or accessories. Keep the answer concise and natural.
""".strip()
    else:
        prompt = f"""
{item_summary}

The user has not added any wardrobe items yet. Give 1 or 2 useful general outfit
ideas for this piece without pretending they own specific items. Name the kinds
of bottoms/tops/shoes/accessories that would work, the color direction, and the
overall vibe. Keep it concise and practical.
""".strip()

    try:
        answer = _call_groq(prompt, temperature=0.65)
        if answer:
            return answer
        return "I couldn't generate a styling suggestion right now. Try again with more wardrobe details."
    except Exception as exc:  # keep an external service failure from crashing the agent
        return (
            "I couldn't reach the styling model, but your listing is still saved. "
            f"Check the GROQ_API_KEY/network connection and try again. ({type(exc).__name__})"
        )


# ── Tool 3: create_fit_card ──────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """Generate a short social-ready caption for the completed outfit."""
    if not isinstance(outfit, str) or not outfit.strip():
        return "I couldn't create a fit card because the outfit suggestion was empty."

    if not isinstance(new_item, dict) or not new_item.get("title"):
        return "I couldn't create a fit card because the selected item details were missing."

    title = new_item.get("title", "the thrifted piece")
    price = new_item.get("price")
    platform = new_item.get("platform", "the resale app")

    prompt = f"""
Create a short 2–4 sentence social caption for this thrifted outfit.

Item: {title}
Price: ${price}
Platform: {platform}
Outfit idea: {outfit.strip()}

Requirements:
- Sound like a real casual OOTD/Instagram/TikTok caption, not a product listing.
- Naturally mention the item name, price, and platform once each.
- Capture the specific outfit vibe and one styling detail.
- Keep it shareable and concise; 0–2 fitting emojis are okay.
- Do not use hashtags unless they genuinely improve the caption.
""".strip()

    try:
        answer = _call_groq(prompt, temperature=0.95)
        if answer:
            return answer
        return "I couldn't generate the fit card text right now. Please try again."
    except Exception as exc:
        # The caption can still be useful even if the external LLM is unavailable.
        return (
            f"Thrift find: {title} for ${price} on {platform}. "
            "The outfit is planned, but the caption generator is temporarily unavailable "
            f"({type(exc).__name__})."
        )
