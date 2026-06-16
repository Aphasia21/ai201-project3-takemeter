"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import re

from tools import search_listings, suggest_outfit, create_fit_card


_SIZE_TOKENS = {"XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"}


def _parse_query(query: str) -> dict:
    """Extract description, size, and max_price from a natural-language query."""
    text = query.strip()
    parsed = {"description": text, "size": None, "max_price": None}

    price_match = re.search(r"(?:under|below|<|less than|max(?:\s*price)?)\s*\$?\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if not price_match:
        price_match = re.search(r"\$\s*(\d+(?:\.\d+)?)", text)
    if price_match:
        parsed["max_price"] = float(price_match.group(1))

    size_match = re.search(r"\bsize\s+([A-Za-z0-9/]+)", text, re.IGNORECASE)
    if size_match:
        parsed["size"] = size_match.group(1).upper()
    else:
        waist_match = re.search(r"\bW\d{2}\b", text, re.IGNORECASE)
        if waist_match:
            parsed["size"] = waist_match.group(0).upper()
        else:
            tokens = re.findall(r"\b[A-Za-z]{1,4}\b", text)
            for tok in tokens:
                if tok.upper() in _SIZE_TOKENS:
                    parsed["size"] = tok.upper()
                    break

    description = text
    description = re.sub(r"(?:under|below|<|less than|max(?:\s*price)?)\s*\$?\s*\d+(?:\.\d+)?", "", description, flags=re.IGNORECASE)
    description = re.sub(r"\$\s*\d+(?:\.\d+)?", "", description)
    description = re.sub(r"\bsize\s+[A-Za-z0-9/]+", "", description, flags=re.IGNORECASE)
    description = re.sub(r"\s+", " ", description).strip(" ,.;:")
    parsed["description"] = description or text

    return parsed


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

_MAX_STEPS = 8


def _decide_next_step(session: dict) -> str:
    """
    Inspect the session and decide what to do next.

    Returns one of: "parse_query", "search", "select_item",
    "suggest_outfit", "create_fit_card", "done".

    The decision is driven by what is already populated in the session — the
    loop is NOT a fixed sequence. For example, an empty search_results list
    routes directly to "done" (with an error), so the downstream tools are
    never invoked.
    """
    if session["error"]:
        return "done"
    if not session["parsed"]:
        return "parse_query"
    if not session["search_results"] and session["selected_item"] is None:
        return "search"
    if session["selected_item"] is None:
        return "select_item"
    if session["outfit_suggestion"] is None:
        return "suggest_outfit"
    if session["fit_card"] is None:
        return "create_fit_card"
    return "done"


def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.

        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].

        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].

        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].

        Step 7: Return the session.

    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
    """
    session = _new_session(query, wardrobe)

    for _ in range(_MAX_STEPS):
        step = _decide_next_step(session)

        if step == "done":
            break

        elif step == "parse_query":
            session["parsed"] = _parse_query(query)

        elif step == "search":
            parsed = session["parsed"]
            session["search_results"] = search_listings(
                description=parsed["description"],
                size=parsed["size"],
                max_price=parsed["max_price"],
            )
            if not session["search_results"]:
                session["error"] = (
                    "No listings matched your request. Try loosening one constraint — "
                    "for example, drop the size filter, raise the price ceiling, or use "
                    "broader keywords (e.g. 'tee' instead of 'vintage graphic tee')."
                )

        elif step == "select_item":
            session["selected_item"] = session["search_results"][0]

        elif step == "suggest_outfit":
            outfit = suggest_outfit(session["selected_item"], wardrobe)
            if not outfit or not outfit.strip():
                session["error"] = (
                    "Could not generate an outfit suggestion. Add a few items to your "
                    "wardrobe and try again."
                )
            else:
                session["outfit_suggestion"] = outfit

        elif step == "create_fit_card":
            fit_card = create_fit_card(session["outfit_suggestion"], session["selected_item"])
            if not fit_card or fit_card.lower().startswith("error"):
                session["error"] = (
                    "Could not generate a fit card. Confirm your outfit selection and "
                    "the chosen item, then try again."
                )
            else:
                session["fit_card"] = fit_card

    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
