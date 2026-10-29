import tools
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe


def test_search_returns_results():
    results = tools.search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(item, dict) for item in results)


def test_search_empty_results():
    results = tools.search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_search_price_filter():
    results = tools.search_listings("jacket", size=None, max_price=50)
    assert results
    assert all(item["price"] <= 50 for item in results)


def test_search_size_filter():
    results = tools.search_listings("track jacket", size="M", max_price=None)
    assert results
    assert all("M" in item["size"].upper() for item in results)


def test_suggest_outfit_with_wardrobe(monkeypatch):
    item = tools.search_listings("vintage graphic tee", size=None, max_price=50)[0]

    def fake_call(prompt, temperature=0.6):
        assert "Baggy straight-leg jeans" in prompt
        assert item["title"] in prompt
        return "Pair it with the baggy straight-leg jeans and chunky white sneakers."

    monkeypatch.setattr(tools, "_call_groq", fake_call)
    result = tools.suggest_outfit(item, get_example_wardrobe())
    assert "baggy" in result.lower()


def test_suggest_outfit_empty_wardrobe(monkeypatch):
    item = tools.search_listings("vintage graphic tee", size=None, max_price=50)[0]

    def fake_call(prompt, temperature=0.6):
        assert "has not added any wardrobe items" in prompt
        return "Try wide-leg jeans, simple sneakers, and a cropped jacket for a 90s look."

    monkeypatch.setattr(tools, "_call_groq", fake_call)
    result = tools.suggest_outfit(item, get_empty_wardrobe())
    assert isinstance(result, str)
    assert result.strip()


def test_suggest_outfit_handles_llm_failure(monkeypatch):
    item = tools.search_listings("vintage graphic tee", size=None, max_price=50)[0]

    def fail_call(prompt, temperature=0.6):
        raise RuntimeError("mock outage")

    monkeypatch.setattr(tools, "_call_groq", fail_call)
    result = tools.suggest_outfit(item, get_example_wardrobe())
    assert "couldn't reach the styling model" in result.lower()


def test_fit_card_empty_outfit():
    item = tools.search_listings("vintage graphic tee", size=None, max_price=50)[0]
    result = tools.create_fit_card("", item)
    assert result == "I couldn't create a fit card because the outfit suggestion was empty."


def test_fit_card_uses_item_details(monkeypatch):
    item = tools.search_listings("vintage graphic tee", size=None, max_price=50)[0]

    def fake_call(prompt, temperature=0.6):
        assert item["title"] in prompt
        assert f"${item['price']}" in prompt
        assert item["platform"] in prompt
        assert temperature >= 0.9
        return "Thrifted the perfect tee and built the whole look around it."

    monkeypatch.setattr(tools, "_call_groq", fake_call)
    result = tools.create_fit_card("Pair it with baggy jeans and sneakers.", item)
    assert isinstance(result, str)
    assert result.strip()
