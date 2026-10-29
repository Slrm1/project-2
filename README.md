# FitFindr — AI Senior Project 2

FitFindr is a multi-tool AI agent for secondhand fashion. A user describes a thrift item they want, optionally adds a size and budget, and FitFindr searches mock listings, selects the best match, suggests how to style it with an existing wardrobe, and generates a shareable fit-card caption.

The full course brief is preserved in [`ASSIGNMENT.md`](./ASSIGNMENT.md), and the implementation spec/architecture is in [`planning.md`](./planning.md).

## Rubric Alignment

This repository is organized around the current **32-point FitFindr brief (25 required + 7 stretch)**. The main graded artifacts are:

- `README.md`: tool inventory, planning-loop logic, state management, error handling, spec reflection, and at least two specific AI-usage examples.
- `planning.md` (**4 pts**): implementation-ready tool specs, conditional planning/state design, error-handling table, text-based Mermaid architecture diagram, milestone-by-milestone AI Tool Plan, and a complete interaction walkthrough.
- Source code: the three required tools in `tools.py`, the conditional agent/state flow in `agent.py`, and the Gradio handler in `app.py`.
- `tests/`: isolated tool tests plus planning/state branch tests, run with `python -m pytest tests/`.
- Demo video (**3–5 minutes**): must show all three tools in one complete workflow, explain state passing, and trigger at least one graceful failure.

The implemented stretch feature is **retry logic with fallback**: when a constrained search returns nothing, FitFindr relaxes constraints in a controlled order and tells the user what changed.

---

## Demo Video

**Demo:** [FitFindr demo video](./demo/20260924-0004-02.1414167.mp4)

The recording shows one complete happy-path interaction, state passing between all three required tools, and a triggered failure/retry path.

---

## Tool Inventory

The documented signatures below match the actual functions in `tools.py`.

### 1. `search_listings(description: str, size: str | None = None, max_price: float | None = None) -> list[dict]`

**Purpose:** Searches `data/listings.json` for relevant secondhand listings. It applies optional size and price filters, scores the remaining items using keyword overlap across listing fields, and returns the best matches first.

**Inputs:**
- `description` (`str`): Natural-language item description, such as `"vintage graphic tee"`.
- `size` (`str | None`): Optional size filter such as `"M"`, `"W30"`, or `"8"`.
- `max_price` (`float | None`): Optional inclusive price ceiling.

**Output:** `list[dict]`. Each result is an original listing dictionary containing `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`. `[]` means no usable match was found.

### 2. `suggest_outfit(new_item: dict, wardrobe: dict) -> str`

**Purpose:** Uses Groq to create one or two styling ideas around the selected thrift listing. With the example wardrobe it names real pieces from the user's closet; with an empty wardrobe it gives general styling advice instead of crashing.

**Inputs:**
- `new_item` (`dict`): The selected listing returned by `search_listings`.
- `wardrobe` (`dict`): A dictionary with an `items` list using the schema in `data/wardrobe_schema.json`.

**Output:** `str`. A non-empty outfit recommendation or a readable failure message if the selected item/API call is unavailable.

### 3. `create_fit_card(outfit: str, new_item: dict) -> str`

**Purpose:** Uses Groq to turn the outfit suggestion into a short social-ready caption. The prompt includes the listing title, price, platform, and outfit details and uses a higher temperature for more varied wording.

**Inputs:**
- `outfit` (`str`): The exact outfit suggestion returned by `suggest_outfit`.
- `new_item` (`dict`): The exact selected listing stored in the session.

**Output:** `str`. A 2–4 sentence fit-card caption. If `outfit` is empty, the function returns a descriptive error string instead of raising an exception.

---

## How the Planning Loop Works

The main loop is `run_agent(query, wardrobe)` in `agent.py`.

1. A fresh session dictionary is created.
2. The query is parsed with regex/string logic into `description`, `size`, and `max_price`.
3. The agent calls `search_listings(description, size, max_price)`.
4. If results exist, the top result is stored as `session["selected_item"]`.
5. If no results exist and a size was provided, the agent automatically retries without the size filter and records that change in `session["adjustments"]`.
6. If the retry still fails and a budget was provided, the agent retries once more without the price ceiling and records that change.
7. If there are still no results, the agent sets `session["error"]` and returns immediately. It does **not** call the outfit or fit-card tools with empty input.
8. On success, the exact selected listing is passed to `suggest_outfit` with the session wardrobe.
9. The exact returned outfit string is stored in `session["outfit_suggestion"]` and passed to `create_fit_card` with the same selected listing.
10. The final caption is stored in `session["fit_card"]` and returned to the Gradio interface.

This is a conditional planning loop rather than a fixed three-call sequence because later tools only run when the earlier state is usable.

---

## State Management

Each interaction uses one session dictionary as the single source of truth. It stores:

- `query`: original user request
- `parsed`: extracted `description`, `size`, and `max_price`
- `search_results`: most recent listing results
- `selected_item`: exact listing chosen from `search_results[0]`
- `wardrobe`: example or empty wardrobe selected in the UI
- `outfit_suggestion`: exact string returned by `suggest_outfit`
- `fit_card`: final caption
- `adjustments`: fallback changes made during retry logic
- `error`: `None` on success or a user-facing early-stop message

State is passed directly between tools. The user never has to re-enter the selected listing or outfit suggestion.

---

## Error Handling Strategy

| Tool / stage | Failure mode | Behavior |
|---|---|---|
| `search_listings` | No matches | Retry without size, then without price. If still empty, return a helpful error and stop before styling. |
| `search_listings` | Dataset loading problem | Return `[]` instead of raising an exception. |
| `suggest_outfit` | Empty wardrobe | Ask the LLM for general styling advice without inventing owned pieces. |
| `suggest_outfit` | Missing item or Groq/API failure | Return a readable failure message instead of crashing the agent. |
| `create_fit_card` | Empty outfit string | Return `I couldn't create a fit card because the outfit suggestion was empty.` |
| `create_fit_card` | Missing item or Groq/API failure | Return an informative fallback/error string. |
| Gradio handler | Blank query | Ask the user to describe what they are looking for and leave later panels blank. |

**Concrete failure example:** `designer ballgown size XXS under $5` produces no relevant listing. FitFindr searches with all constraints, retries without size, retries without the price ceiling, then stops with a helpful message. `suggest_outfit` and `create_fit_card` are never called for that interaction.

---

## Stretch Feature

### Retry logic with fallback

FitFindr implements the retry/fallback stretch feature. When the initial search returns nothing, it loosens constraints in a controlled order instead of immediately failing. The UI reports the exact adjustment(s) that were made so the user knows why the returned result may not match every original filter.

---

## Testing

Tests are in `tests/` and use `pytest`. Network-dependent Groq calls are monkeypatched in unit tests so the behavior can be tested without making live API requests.

Run all tests from the repository root:

```bash
python -m pytest tests/
```

A local verification of the implemented logic/test suite completed successfully with **13 passing tests**. The final cloned repository should still be tested once more in the submission environment after dependencies are installed.

Coverage includes:
- successful listing search
- zero-result search
- price filtering
- size filtering
- styling with a populated wardrobe
- styling with an empty wardrobe
- simulated LLM failure
- empty fit-card input
- query parsing
- exact state passing between tools
- early termination when search fails
- automatic recovery when relaxing the size constraint

---

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Mac/Linux:

```bash
source .venv/bin/activate
```

Windows Git Bash:

```bash
source .venv/Scripts/activate
```

Windows Command Prompt:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the repository root:

```env
GROQ_API_KEY=your_key_here
```

`.env` is ignored by Git and should never be committed.

Run the interface:

```bash
python app.py
```

Open the local URL printed by Gradio in the terminal.

---

## AI Usage

### Instance 1 — tool implementation

I gave ChatGPT the completed Tool 1–3 specifications from `planning.md`, the starter function signatures, the listing fields, and the wardrobe schema. I directed it to implement one tool at a time while preserving the starter interfaces and failure behavior. Before using the generated code, I checked that `search_listings` used `load_listings()` instead of rewriting the loader, that empty searches returned `[]`, that empty wardrobes still produced styling behavior, and that `create_fit_card` guarded against an empty outfit before making an LLM call.

I revised the generated approach by separating the Groq call into `_call_groq`. This makes external-service failures easier to handle and allows pytest to monkeypatch the network call instead of depending on a live API key.

### Instance 2 — planning loop and state management

I gave ChatGPT the Planning Loop, State Management, Error Handling, and Mermaid Architecture sections from `planning.md` plus the starter `agent.py`. I directed it to implement the loop so later tools only run when previous results are usable.

I revised the implementation to add `session["adjustments"]` and two controlled fallback searches. I also added tests that use object identity (`is`) to verify that the exact `selected_item` stored in session state is the object passed to `suggest_outfit` and `create_fit_card`, rather than reconstructing the item between steps.

---

## Spec Reflection

**How the spec helped:** Writing the tool inputs, outputs, and failure behavior first made the state flow straightforward. Because `selected_item` and `outfit_suggestion` were explicitly defined before coding, the planning loop could pass exact values between tools without adding extra prompts or hardcoded replacements.

**How implementation diverged from the initial starter:** The starter's basic happy path stopped immediately when search returned nothing. I extended that behavior with the retry/fallback stretch feature. The final implementation first removes the size restriction and then, if necessary, removes the price ceiling. This change keeps the agent useful while still making the fallback visible to the user through `session["adjustments"]`.

---

## Submission Checklist

- [x] Official FitFindr starter files added
- [x] `planning.md` completed before implementation
- [x] Three required tools implemented
- [x] Planning loop and state management implemented
- [x] Required failure modes handled
- [x] Retry/fallback stretch feature implemented
- [x] Pytest tests added
- [x] README documents tools, loop, state, errors, reflection, and AI usage
- [x] Local logic/test-suite verification completed (13 tests passed)
- [ ] Run `python -m pytest tests/` once more after cloning/installing dependencies in the final submission environment
- [x] Record and link the 3–5 minute demo video
