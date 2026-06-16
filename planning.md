# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.
FitFindr is an app to help users to find clothings from online listings and suggest outfit based on current wardrobe and eventuall create a fit 
---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
This tool helps user to find relevant fashion pieces from the listing. This tool searches the mock listings dataset and returns matching items. 

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): Y2K Baby Tee
- `size` (str): S
- `max_price` (float): $50

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
Returns 3 matching listings sorted by relevance. It contains desciption of the item incluidng name, description, size, price, condition and color. 

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
If search_listings returns no results, automatically retry with loosened constraints (e.g., remove size filter) and inform the user what was adjusted. After search_listings runs, check if results is empty. If yes, set an error message in the session and return early. If no, set selected_item = results[0] and proceed to suggest_outfit." Your description should be specific enough that someone else could implement it from your words alone.
---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Given a specific item and the user's current wardrobe, suggests one or more complete outfit combinations. Must handle an empty or minimal wardrobe. User should be able to choose from the items generated in search_listings to pair with their selected wardrobe and then this tool will suggest outfit.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): Each one of the items from search_listings output will be used here separately.
- `wardrobe` (dict): the "items" from data/wardrobe_schema.json.
By default, we use the "example_wardrobe", but if user choose empty wardrobe, we should be able to handle it by putting listing into the empty wardrobe and suggest output.

**What it returns:
A list of strings which includes the outfit items and a few sentences of suggestion of how to wear and style it. Example, returns: "Pair this with your wide-leg jeans and platform Docs for a classic 90s grunge look. Roll the sleeves once and tuck the front corner slightly for shape."

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
Check if it's due to lack of items in the wardrobe, then tell the user the select the more items to construct outfit. If it's due to internal constraints, then widened the model selection and try to provide suggest what items to include. 
---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Generates a short, shareable description of a complete outfit — the kind of thing someone would caption an Instagram post with. Must produce something different each time for different inputs.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (list): the final items that user selected and the final outfit user liked.

**What it returns:**
<!-- Describe the return value -->
a string of instagram ready decription of the complete outfit that user selects. 

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
Check back on tool 1 and tool 2 inputs. Tell the user needs to select final items and outfit to generate fit card.
---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->
Price comparison tool: Add a fourth tool that, given an item, estimates whether the price is fair based on comparable listings in the dataset.
Trend awareness: Add a tool that checks recent posts or tags on a public fashion platform to surface what styles are currently popular in the user's size range.
---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
Information returned by one tool must be available to subsequent tools in the same session. For example, the item found by search_listings should flow into suggest_outfit without the user having to re-enter it.
Use a loop (or equivalent reasoning mechanism) that selects which tools to call based on what's been returned so far. The agent should not call all tools in a fixed sequence regardless of context — it should respond to what it receives. 
---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
The state flow is from tool 1 to tool 2 to tool 3. First, app should store the output of tool 1 and will be used in tool 2. The app should also store the final selected output from tool 2 to be used in tool 3. if user go back to generate tool 1 again then the stored infomation will be refreshed and used for tool 2. The same if user go back to change tool 2 final output, then new information will be stored for tool 2 and be used in tool 3. 
---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Tell user to choose a different requirements|
| suggest_outfit | Wardrobe is empty |Tell user to put items into the wardrobe in order to suggest outfit.|
| create_fit_card | Outfit input is missing or incomplete | Tell user to select his final item and outfit in order to generate fit card |

Error path: If search_listings returns nothing, FitFindr tells the user what to try differently and stops — it does not call suggest_outfit with empty input.
Error handling for each tool: Every tool must handle its own failure mode. "Fail silently" or "crash the agent" are not acceptable error handling strategies. At minimum: if a tool returns an empty result or encounters an error, the agent should communicate this to the user and either try a fallback strategy or ask for more information. Document your error handling strategy in your README.
---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->
User query
    │
    ▼
Planning Loop ───────────────────────────────────────────┐
    │                                                    │
    ├─► search_listings(description, size, max_price)    │
    │       │ results=[]                                 │
    │       ├──► [ERROR] "No listings found..." → return │
    │       │                                            │
    │       │ results=[item, ...]                        │
    │       ▼                                            │
    │   Session: selected_item = results[0]              │
    │       │                                            │
    ├─► suggest_outfit(selected_item, wardrobe)          │
    │       │                                            │
    │   Session: outfit_suggestion = "..."               │
    │       │                                            │
    └─► create_fit_card(outfit_suggestion, selected_item)│
            │                                            │
        Session: fit_card = "..."                        │
            │                                            └─ error path returns here
            ▼
        Return session
---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

- **search_listings (Claude):** I'll paste the **Tool 1** block (the three inputs `description`/`size`/`max_price`, the return-value description, and the loosen-and-retry failure mode) plus the `load_listings()` signature from the data loader and one example row from `data/listings.json` so the field names are pinned. I'll ask Claude to implement `search_listings()` that filters by all three params, treats empty/None values as "no preference," and returns the top 3 matches sorted by relevance. Before running the code I'll read the diff and check: (1) each of the 3 params is actually applied to the filter, (2) empty strings/None skip the filter rather than matching literally, (3) the no-results retry actually drops a constraint and tells the user what was dropped (per the **Tool 1** failure mode). Then I'll run 3 queries by hand — an exact match ("Y2K Baby Tee, S, $50"), a partial query (only `description="tee"`), and a query I know returns zero so I can confirm the retry kicks in.

- **suggest_outfit (Claude):** Once I finish the **Tool 2** block, I'll give Claude that spec, the `data/wardrobe_schema.json` example, and one sample row from `search_listings`'s output so the dict shapes are concrete. I'll ask for a function that takes a single `new_item` dict + a `wardrobe` dict and returns a styling suggestion. Verification: confirm the LLM prompt the function builds includes BOTH the new item AND the wardrobe items (not just one), confirm the empty-wardrobe branch from the **Error Handling** table is reachable in the code, and run it against (a) the example wardrobe, (b) an empty wardrobe, (c) a one-item wardrobe — for each, check the response actually references the items I passed in rather than inventing new ones.

- **create_fit_card (Copilot for boilerplate, Claude for the prompt):** Once the **Tool 3** block is filled, I'll use Copilot to scaffold the function signature and the markdown/image assembly, and Claude to draft any LLM prompt the card uses. I'll feed Claude the **Tool 3** spec and the upstream return shapes from `suggest_outfit` and `search_listings`. Verification: pass a complete outfit dict and confirm every field from the **Tool 3** spec appears in the rendered card; pass an outfit missing one field and confirm the error path from the **Error Handling** table triggers (no silent blanks, no crashes).

**Milestone 4 — Planning loop and state management:**

- **Planning loop (Claude):** I'll give Claude the **Planning Loop** section, the ASCII **Architecture** diagram (lines 120–139 of planning.md showing the `search_listings → suggest_outfit → create_fit_card` flow with session writes between each), the **A Complete Interaction** walkthrough, and the three tool signatures from Milestone 3. I'll ask it to implement a loop that parses user intent → calls `search_listings` → picks an item → calls `suggest_outfit` with that item + wardrobe → calls `create_fit_card`. Before trusting the output I'll trace the **A Complete Interaction** example through the generated code line by line and confirm each diagram arrow has a matching code path; I'll also verify tool selection actually branches on prior results (not a hard-coded sequence) so the search_listings no-results branch shown in the diagram still routes correctly. Then I'll run the example query end-to-end plus one variant that forces the empty-wardrobe path.

- **State management (Claude):** I'll give Claude the **State Management** section plus the planning-loop code from the previous step and ask it to add a session object that carries `selected_item`, `outfit_suggestion`, and `fit_card` between tool calls — the exact three slots the **Architecture** diagram shows being written. Verification: grep the generated code to confirm no downstream tool reads from user input for data that should come from session state, and run the example interaction twice in the same session to confirm state persists across turns and resets cleanly when a new session starts.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
The agent first extracts the inputs from user query. In the example case, the agent will extract decirption is vintage graphic tee, the max_price is $30, the size is unknow. The style user likes is the combination style tags of tee, baggy jeans and chunky sneakers. Then the agent will run tool 1 search_listings function to find the top 3 items matches the user request. Then those top 3 items full dictionary information will be saved and passed on to the next step for tool 2 usage. Also, the agent will saved the current wardrobe with baggy jeans and chunky sneakers in this example. Any current items that the user has should be saved. 
Style profile memory: Allow the agent to remember a user's style preferences across sessions, so they don't have to re-describe their wardrobe every time.

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
Once step 1 is done, user can choose each of items, and the current wardrobe from tool 1 as inputs to tool 2, then run suggest_outfit to generate output. If no current wardrobe is saved, we can use use the "example_wardrobe" from data/wardrobe_schema.json. Once the agent generate the outfit, agent should let the user to choose their final selected item and final outfit, and then save them for tool 3. 

**Step 3:**
<!-- Continue until the full interaction is complete -->
Based on final outfit from tool 3 as inputs, the agent will run create_fit_card and save the output. 

**Final output to user:**
<!-- What does the user actually see at the end? -->
The agent will output the selected final item, the final outfit and the fit card results.
