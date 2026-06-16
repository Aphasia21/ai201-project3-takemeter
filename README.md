# FitFindr

FitFindr is a thrift-shopping agent. The user types one natural-language query; the agent searches a mock secondhand listings dataset, suggests an outfit pairing the find with the user's existing wardrobe, and writes a short Instagram-ready caption — three coordinated tool calls, three output panels in a Gradio UI.

## Project Structure

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example + empty templates
├── utils/
│   └── data_loader.py         # load_listings, get_example_wardrobe, get_empty_wardrobe
├── tests/
│   └── test_tools.py          # pytest tests, one per tool failure mode
├── tools.py                   # The three tools
├── agent.py                   # Planning loop — run_agent() + _decide_next_step()
├── app.py                     # Gradio UI — handle_query()
├── planning.md                # Spec, agent diagram, AI tool plan
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

LLM tools use Groq's `llama-3.3-70b-versatile`.

## Running FitFindr

```bash
python app.py            # launch the Gradio UI (default http://localhost:7860)
python agent.py          # CLI test: happy path + no-results path
pytest tests/            # tool tests
```

## Tool Inventory

The three tools live in `tools.py`. Signatures below match the actual function definitions exactly.

### `search_listings(description: str, size: str | None = None, max_price: float | None = None) -> list[dict]`

**Purpose.** Filter the mock listings dataset and surface the most relevant items for a search query.

**Inputs.**
- `description` (`str`) — keywords describing what the user wants (e.g. `"vintage graphic tee"`)
- `size` (`str | None`) — size string to filter by; `None` skips the size filter
- `max_price` (`float | None`) — inclusive price ceiling; `None` skips the price filter

**Output.** `list[dict]` — listings sorted by relevance, highest score first. Each dict has the listings.json fields: `id, title, description, category, style_tags, size, condition, price, colors, brand, platform`. Returns `[]` (never raises) when nothing matches.

**Logic.** Drop listings over `max_price`, drop listings whose `size` doesn't contain the query size (case-insensitive substring), score each remaining listing by token overlap between `description` and the listing's title/description/style_tags/colors/category/brand, drop zero-score listings, sort descending.

### `suggest_outfit(new_item: dict, wardrobe: dict) -> str`

**Purpose.** Generate a 4–7 sentence styling suggestion that pairs the new item with the user's existing pieces.

**Inputs.**
- `new_item` (`dict`) — a listing dict from `search_listings`
- `wardrobe` (`dict`) — wardrobe with an `items` key holding a list of pieces (may be empty)

**Output.** `str` — non-empty styling paragraph from the LLM (Groq `llama-3.3-70b-versatile`, temperature 0.6).

**Logic.** If `wardrobe["items"]` is non-empty, build a prompt listing each piece by name and ask for 1–2 outfits naming those specific pieces. If empty, ask for general styling categories (e.g. "baggy jeans, chunky sneakers") instead of named pieces.

### `create_fit_card(outfit: str, new_item: dict) -> str`

**Purpose.** Produce a casual 2–4 sentence OOTD caption mentioning the item, price, and platform once each.

**Inputs.**
- `outfit` (`str`) — the outfit suggestion from `suggest_outfit`
- `new_item` (`dict`) — the same listing dict used for `suggest_outfit`

**Output.** `str` — either the caption (LLM, temperature 0.9 for variance across reruns) or the literal string `"Error: cannot create a fit card — no outfit suggestion was provided."` when `outfit` is empty/whitespace.

## Planning Loop

`run_agent()` in `agent.py` is a state-driven dispatch loop. Each iteration:

1. Calls `_decide_next_step(session)` to choose what to do.
2. Executes that one step and writes its result into the session.
3. Loops again — the next decision is recomputed from the new session.

`_decide_next_step` is pure conditional logic over the session dict:

```python
if session["error"]:                                          return "done"
if not session["parsed"]:                                     return "parse_query"
if not session["search_results"] and selected_item is None:   return "search"
if session["selected_item"] is None:                          return "select_item"
if session["outfit_suggestion"] is None:                      return "suggest_outfit"
if session["fit_card"] is None:                               return "create_fit_card"
return "done"
```

Two consequences fall out of this:

- **The agent responds to results, not a script.** If `search_listings` writes `error` (because results were empty), the next iteration sees `error` set and returns `"done"` — `suggest_outfit` and `create_fit_card` are never entered.
- **Out-of-order completion is handled.** The decision is a precondition check, not a step counter. If a future change pre-populates `selected_item` from a different source, the loop simply skips `select_item` and proceeds to `suggest_outfit`.

A `_MAX_STEPS = 8` cap protects against a logic bug spinning the loop indefinitely.

## State Management

A single `session` dict (created by `_new_session(query, wardrobe)`) is the only state shared across tools. The user types one query; everything else flows through this dict — by reference, not copied. Identity (`is`) checks confirmed the agent passes the exact same `selected_item` dict into both `suggest_outfit` and `create_fit_card`.

| Field | Type | Written when | Read by |
|---|---|---|---|
| `query` | `str` | session creation | `parse_query` step |
| `parsed` | `dict` | `parse_query` step | `search` step |
| `search_results` | `list[dict]` | `search` step | `select_item` step |
| `selected_item` | `dict` | `select_item` step | `suggest_outfit` step, `create_fit_card` step, UI |
| `wardrobe` | `dict` | session creation (from radio choice) | `suggest_outfit` step |
| `outfit_suggestion` | `str` | `suggest_outfit` step | `create_fit_card` step, UI |
| `fit_card` | `str` | `create_fit_card` step | UI |
| `error` | `str \| None` | any failure branch | loop (routes to `"done"`), UI |

`app.py`'s `handle_query` reads `session["error"]` first; on success it formats `session["selected_item"]` into the listing panel and passes `outfit_suggestion` and `fit_card` straight through to the other two panels.

## Error Handling

Each tool owns its failure mode and never crashes the agent. The loop turns a tool's "I couldn't" return value into a user-facing recovery message.

### `search_listings` — no results match the query

**Tool behavior.** Returns `[]`. No exception, no partial results.

**Agent response.** The `search` step in `run_agent` sees the empty list, writes a recovery hint into `session["error"]` (*"loosen one constraint — drop the size filter, raise the price ceiling, or use broader keywords"*), and the next loop iteration short-circuits to `"done"`.

**Concrete test result.** Running `python agent.py` on the built-in no-results case (`"designer ballgown size XXS under $5"`) produces:

```
session['search_results']    = []
session['selected_item']     = None
session['outfit_suggestion'] = None
session['fit_card']          = None
session['error']             = No listings matched your request. Try loosening one constraint...
Downstream tool calls observed: []
```

`suggest_outfit` and `create_fit_card` were never invoked — verified with a spy wrapping the imported names.

### `suggest_outfit` — wardrobe is empty

**Tool behavior.** Checks `wardrobe["items"]` first. If empty, switches to a general-styling prompt (asking for outfit *categories* the user could pair, not named pieces) and returns a non-empty string.

**Agent response.** The non-empty string flows through the session like any other suggestion — `create_fit_card` runs normally.

**Concrete test result.** `tests/test_tools.py::test_suggest_outfit_empty_wardrobe_does_not_crash` passes: calling `suggest_outfit(item, get_empty_wardrobe())` returns a styling paragraph beginning *"With the Y2K Baby Tee, you can create a nostalgic and playful outfit by pairing it with high-waisted baggy jeans..."* — no exception, no empty string.

### `create_fit_card` — outfit missing or incomplete

**Tool behavior.** If `outfit` is empty or whitespace-only, returns the literal `"Error: cannot create a fit card — no outfit suggestion was provided."` — no LLM call, no exception.

**Agent response.** The loop's `create_fit_card` step inspects the return; if it starts with `"error"` (case-insensitive), it writes a user-facing message to `session["error"]` and stops.

**Concrete test result.** `tests/test_tools.py::test_create_fit_card_empty_outfit_returns_error_string` and `test_create_fit_card_whitespace_outfit_returns_error_string` both pass. `create_fit_card("   \n  ", item)` returns the error string instead of crashing.

## Spec Reflection

**What the spec helped with.** The ASCII architecture diagram in `planning.md` showed exactly which session field each tool writes and reads — `search_listings → selected_item → suggest_outfit → outfit_suggestion → create_fit_card → fit_card` with the error path branching out of the search step. That diagram translated directly into the `_decide_next_step` decision table; I didn't have to re-derive the data flow from scratch when writing the loop.

**Where the implementation diverged from the spec.**

- *Spec said:* `search_listings` "automatically retry with loosened constraints (e.g., remove size filter) and inform the user what was adjusted."
- *Implementation does:* return `[]` and let the agent loop write a recovery hint asking the user to loosen one constraint.
- *Why.* An auto-retry that silently drops the size filter could surface a wrong-size item as if it matched what the user asked for, which is worse than honestly reporting no match. Pushing the choice back to the user (via a specific hint) keeps the agent honest. If we want auto-retry later, it belongs in the loop's `search` step as a second iteration with widened parameters, not buried inside the tool.

A second smaller divergence: the spec said *"Returns 3 matching listings"* — the implementation returns *all* matches sorted by relevance, and the UI displays only the top one. Capping inside the tool would hide legitimate matches if we ever surface a results list; capping at the UI is reversible, capping in the tool isn't.

## AI Usage

### 1. Implementing `search_listings` from the Tool 1 spec

**What I directed Claude to do.** Implement `search_listings(description, size, max_price)` using `load_listings()` from `utils/data_loader.py`. Filter by `size` (case-insensitive) and `max_price`, score remaining listings by keyword overlap, drop zero-score listings, sort descending. Return `[]` on no match (don't raise).

**What I overrode.** Claude's first pass treated `description` as a substring search against the listing `title` only. I rewrote the scoring to tokenize the description and score against the full set of searchable fields (`title`, `description`, `style_tags`, `colors`, `category`, `brand`), filter tokens by length > 2 to drop stop-word noise, and use set intersection. Then I ran three test queries by hand — `"vintage graphic tee"` with `max_price=30`, `"jeans"` with `size="W30"`, and a deliberately zero-result query — before trusting the function. The case-insensitive size match also came from this verification step: `"W30"` had to match `"W30 L30"` even though they're not equal strings.

### 2. Writing the `create_fit_card` variance test

**What I directed Claude to do.** Write pytest tests for each tool, covering happy paths and the documented failure modes (no-results, empty wardrobe, empty outfit).

**What I revised.** The user-supplied assignment said *"Run it several times on the same input and verify the outputs vary; if they're identical, increase the LLM temperature."* I added that as an inline check before pytest, not as a test, because three real LLM round-trips per pytest run is slow and flaky. The inline check at temperature 0.6 produced 2/3 unique captions in one run — close enough to "varying," but not reliable. I bumped `create_fit_card`'s temperature to 0.9 (kept `suggest_outfit` at 0.6 since the styling text doesn't need to vary much). After the bump, three reruns produced three different captions; that gave me enough confidence to ship.

### 3. Implementing the planning loop

**What I directed Claude to do.** Implement `run_agent()` following the architecture diagram in `planning.md` and the TODO step list already in `agent.py`. The Planning Loop section of `planning.md` quoted the rubric line *"Use a loop (or equivalent reasoning mechanism) that selects which tools to call based on what's been returned so far."*

**What I revised.** The first pass was straight-line code with early `return`s — functionally correct, but it didn't visibly *look* like a loop, and "loop or equivalent reasoning mechanism" was an explicit grading point. I refactored it into a `for _ in range(_MAX_STEPS)` dispatch loop with a separate `_decide_next_step(session)` that returns the next step's name based on which session fields are populated. That made the conditional logic explicit (the rules became a readable list) and gave me a clean place to spy on the decision in tests.
