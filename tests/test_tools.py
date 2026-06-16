from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


def test_search_size_filter_case_insensitive():
    results = search_listings("jeans", size="w30", max_price=None)
    assert len(results) > 0
    assert all("w30" in item["size"].lower() for item in results)


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def _sample_item():
    return search_listings("graphic tee", size=None, max_price=50)[0]


def test_suggest_outfit_with_wardrobe():
    out = suggest_outfit(_sample_item(), get_example_wardrobe())
    assert isinstance(out, str)
    assert out.strip() != ""


def test_suggest_outfit_empty_wardrobe_does_not_crash():
    out = suggest_outfit(_sample_item(), get_empty_wardrobe())
    assert isinstance(out, str)
    assert out.strip() != ""


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def test_create_fit_card_empty_outfit_returns_error_string():
    card = create_fit_card("", _sample_item())
    assert isinstance(card, str)
    assert card.lower().startswith("error")


def test_create_fit_card_whitespace_outfit_returns_error_string():
    card = create_fit_card("   \n  ", _sample_item())
    assert isinstance(card, str)
    assert card.lower().startswith("error")


def test_create_fit_card_happy_path():
    item = _sample_item()
    card = create_fit_card("Pair with baggy jeans and chunky sneakers.", item)
    assert isinstance(card, str)
    assert card.strip() != ""
    assert not card.lower().startswith("error")
