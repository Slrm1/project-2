import agent
from utils.data_loader import get_example_wardrobe


def test_parse_query_extracts_constraints():
    parsed = agent._parse_query("I'm looking for a vintage graphic tee under $30, size M")
    assert "vintage graphic tee" in parsed["description"].lower()
    assert parsed["size"] == "M"
    assert parsed["max_price"] == 30.0


def test_happy_path_passes_state_between_tools(monkeypatch):
    listing = {
        "id": "x1",
        "title": "Vintage Graphic Tee",
        "description": "faded graphic tee",
        "category": "tops",
        "style_tags": ["vintage", "graphic tee"],
        "size": "M",
        "condition": "good",
        "price": 22.0,
        "colors": ["black"],
        "brand": None,
        "platform": "depop",
    }
    seen = {}

    def fake_search(description, size=None, max_price=None):
        seen["search"] = (description, size, max_price)
        return [listing]

    def fake_outfit(new_item, wardrobe):
        seen["outfit_item"] = new_item
        return "Wear it with baggy jeans and chunky sneakers."

    def fake_card(outfit, new_item):
        seen["card_outfit"] = outfit
        seen["card_item"] = new_item
        return "fit card"

    monkeypatch.setattr(agent, "search_listings", fake_search)
    monkeypatch.setattr(agent, "suggest_outfit", fake_outfit)
    monkeypatch.setattr(agent, "create_fit_card", fake_card)

    session = agent.run_agent(
        "vintage graphic tee under $30, size M",
        get_example_wardrobe(),
    )

    assert session["error"] is None
    assert session["selected_item"] is listing
    assert seen["outfit_item"] is session["selected_item"]
    assert seen["card_item"] is session["selected_item"]
    assert seen["card_outfit"] == session["outfit_suggestion"]
    assert session["fit_card"] == "fit card"


def test_no_results_stops_before_later_tools(monkeypatch):
    calls = {"search": 0, "outfit": 0, "card": 0}

    def fake_search(description, size=None, max_price=None):
        calls["search"] += 1
        return []

    def fake_outfit(new_item, wardrobe):
        calls["outfit"] += 1
        return "should not happen"

    def fake_card(outfit, new_item):
        calls["card"] += 1
        return "should not happen"

    monkeypatch.setattr(agent, "search_listings", fake_search)
    monkeypatch.setattr(agent, "suggest_outfit", fake_outfit)
    monkeypatch.setattr(agent, "create_fit_card", fake_card)

    session = agent.run_agent(
        "designer ballgown size XXS under $5",
        get_example_wardrobe(),
    )

    assert session["error"] is not None
    assert session["selected_item"] is None
    assert session["fit_card"] is None
    assert calls["search"] == 3
    assert calls["outfit"] == 0
    assert calls["card"] == 0
    assert len(session["adjustments"]) == 2


def test_retry_without_size_can_recover(monkeypatch):
    listing = {
        "id": "x2",
        "title": "90s Track Jacket",
        "description": "navy track jacket",
        "category": "outerwear",
        "style_tags": ["90s"],
        "size": "L",
        "condition": "good",
        "price": 35.0,
        "colors": ["navy"],
        "brand": None,
        "platform": "poshmark",
    }

    def fake_search(description, size=None, max_price=None):
        return [] if size is not None else [listing]

    monkeypatch.setattr(agent, "search_listings", fake_search)
    monkeypatch.setattr(agent, "suggest_outfit", lambda item, wardrobe: "outfit")
    monkeypatch.setattr(agent, "create_fit_card", lambda outfit, item: "card")

    session = agent.run_agent(
        "90s track jacket size M under $50",
        get_example_wardrobe(),
    )

    assert session["error"] is None
    assert session["selected_item"] is listing
    assert session["adjustments"]
    assert "without the size filter" in session["adjustments"][0]
