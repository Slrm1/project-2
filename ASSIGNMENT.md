# Show What You Know: FitFindr

⏰ ~8–9 hours total

> **Brief synchronization note (September 22, 2026):** This repository copy is aligned to the course brief supplied for the current FitFindr submission. The implementation-facing requirements are reflected in `planning.md`, and the graded submission evidence is organized in `README.md`.


Thrifting is not just a way to shop — it's a whole process. You're searching across multiple platforms, trying to picture how something fits with what you already own, figuring out if the price is actually good, and ultimately deciding whether it's worth it. That process involves a lot of searching, comparing, and reasoning that could be significantly more useful with the right tools.

In this project, you'll build **FitFindr**: a multi-tool AI agent that helps users find secondhand pieces and figure out how to wear them. The agent orchestrates a set of tools in response to a natural language request — searching listings, evaluating fit against an existing wardrobe, and generating a shareable outfit description — while handling the messy reality of what happens when a tool fails or returns nothing useful.

Last week you built a retrieval system. This week you're building something that acts: an agent that decides which tools to call, in what order, and what to do when things don't go as planned.

## 🗺️ How It's Graded

A detailed breakdown of graded features and points can be found on the course grading page — **32 points total (25 required + 7 stretch)**.

## 📋 Deliverables & Format

Your `README.md` is the graded artifact for the Submitting checklist. Everything in that checklist except the repo link, the video, and `planning.md` lives there.

`planning.md` is graded separately, on its own contents (4 pts). Your tool inventory, planning loop and state management, error-handling table and interaction walkthrough, and your architecture diagram together with an AI Tool Plan are scored from `planning.md` itself. The diagram must be ASCII/text art or a Mermaid block; an embedded image or screenshot is not accepted.

Your documented tool inventory must match your actual code. Parameter names, types, and return values in the README have to agree with your real function signatures — a mismatch costs points.

`planning.md` must live in the repo root, be written before implementation, and be updated before stretch features.

Demo video: **3–5 minutes**, linked from your README.

## 🎯 Goals

By completing this project, you will be able to:

- Design a set of tools with clearly defined interfaces, inputs, and outputs.
- Implement a planning loop that determines which tools to call and when.
- Manage state across multiple tool calls within a single session.
- Build error handling for each tool that keeps the agent useful when something breaks.
- Document agent behavior so someone reading your README understands what the agent is doing, not just that it's working.

## ✅ Required Features

### Three or more tools with defined interfaces

Build at least 3 distinct tools. Each tool must have a clearly defined function signature: what it accepts as input and what it returns.

```python
search_listings(description, size, max_price)
```

Searches the mock listings dataset and returns matching items. Must handle the case where no matches are found.

```python
suggest_outfit(new_item, wardrobe)
```

Given a specific item and the user's current wardrobe, suggests one or more complete outfit combinations. Must handle an empty or minimal wardrobe.

```python
create_fit_card(outfit, new_item)
```

Generates a short, shareable description of a complete outfit — the kind of thing someone would caption an Instagram post with. Must produce something different each time for different inputs.

### Planning loop

Your agent must use a loop or equivalent reasoning mechanism that selects which tools to call based on what's been returned so far. The agent should not call all tools in a fixed sequence regardless of context. Document how your planning loop works in your README.

### State management across tool calls

Information returned by one tool must be available to subsequent tools in the same session. For example, the item found by `search_listings` should flow into `suggest_outfit` without the user having to re-enter it. Show this in your demo video.

### Error handling for each tool

Every tool must handle its own failure mode. Failing silently or crashing the agent is not acceptable. At minimum, if a tool returns an empty result or encounters an error, the agent should communicate this to the user and either try a fallback strategy or ask for more information. Document your error handling strategy in your README.

### Multi-step workflow

Your demo must include at least one complete multi-step interaction that uses all 3 required tools in sequence — from initial query to final fit card.

## Stretch Features

Complete any of these for extra credit. Update your `planning.md` before starting each one.

- **Price comparison tool:** Add a fourth tool that, given an item, estimates whether the price is fair based on comparable listings in the dataset.
- **Style profile memory:** Allow the agent to remember a user's style preferences across sessions.
- **Trend awareness:** Add a tool that checks recent posts or tags on a public fashion platform to surface what styles are currently popular in the user's size range.
- **Retry logic with fallback:** If `search_listings` returns no results, automatically retry with loosened constraints and inform the user what was adjusted.

## 💡 Hints

- Design your tools on paper before implementing them.
- Test tools in isolation first.
- Your planning loop does not have to be complex to be real; its behavior simply needs to change based on what was returned.
- Error handling is a design decision before it's a coding problem.
- The fit card should sound like something worth sharing, not like a product description.

## 🛠️ Tools and Setup

This project uses the same free LLM from Project 1 — no new accounts or credits required.

### Recommended stack

| Component | Tool | Notes |
|---|---|---|
| LLM | Groq (`meta-llama/llama-4-scout-17b-16e-instruct`) | Free tier — same account as Project 1 |
| Mock data | Provided in starter repo | No external API needed |

### Getting started

Fork the FitFindr starter repo, then clone your fork locally.

Create and activate a virtual environment from inside your cloned repo:

```bash
python -m venv .venv
source .venv/bin/activate          # Mac/Linux
source .venv/Scripts/activate      # Windows (Git Bash)
# or: .venv\Scripts\activate       # Windows (Command Prompt)
```

You should see `(.venv)` in your terminal prompt.

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in your repo root. This file should be listed in `.gitignore` and should never be committed.

```env
GROQ_API_KEY=your_key_here
```

## Milestone 1: Explore the Starter Repo and Understand the Problem

⏰ ~30 min

A complete FitFindr interaction looks like this:

**User:** “I'm looking for a vintage graphic tee under $30, size M. I mostly wear baggy jeans and chunky sneakers.”

**Step 1 — Search:**

```python
search_listings("vintage graphic tee", size="M", max_price=30.0)
```

Returns matching listings sorted by relevance. FitFindr selects the top result.

**Step 2 — Suggest outfit:**

```python
suggest_outfit(new_item=<selected item>, wardrobe=<user wardrobe>)
```

Returns a complete styling suggestion using the user's wardrobe.

**Step 3 — Fit card:**

```python
create_fit_card(outfit=<suggestion>, new_item=<selected item>)
```

Returns a short shareable caption.

**Error path:** If `search_listings` returns nothing, FitFindr tells the user what to try differently and stops. It must not call `suggest_outfit` with empty input.

Tasks:

1. Open `data/listings.json` and inspect 5–10 listings. Note fields: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`.
2. Open `data/wardrobe_schema.json` and understand the wardrobe structure.
3. Read `utils/data_loader.py`. Use `load_listings()`, `get_example_wardrobe()`, and `get_empty_wardrobe()` rather than rewriting them.
4. Write a 2–3 sentence description of what FitFindr needs to do and add it to the **A Complete Interaction** section of `planning.md`.

### Checkpoint

- You can describe the listings data structure from memory.
- You understand the difference between `get_example_wardrobe()` and `get_empty_wardrobe()`.

## Milestone 2: Write Your Spec Before Any Code

⏰ ~1 hour

Open `planning.md` from the starter repo and replace each prompt with specific, implementation-ready content.

For each of the three required tools, document:

- What it does.
- Exact input parameter names, types, and meanings.
- What it returns.
- What the agent does if it fails or returns nothing.

For the planning loop, describe the actual conditional logic. Example:

> After `search_listings` runs, check whether the results are empty. If yes, set an error message in the session and return early. If no, set `selected_item = results[0]` and proceed to `suggest_outfit`.

### Architecture diagram requirement

Add an ASCII or Mermaid diagram to the `## Architecture` section of `planning.md`. It must include the user, planning loop, each tool, session state, data flow, and a visible error branch.

Example:

```text
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
```

### AI Tool Plan

For each milestone, document:

- Which AI tool you'll use.
- Which specific `planning.md` sections or diagrams you'll provide as input.
- What you expect the AI tool to produce.
- How you'll verify the result matches your spec.

The plan must be specific, not just “I'll use AI to help me code.”

### Interaction walkthrough

At the bottom of `planning.md`, trace the example query step-by-step through all three tools, including exact inputs, returned values, state updates, and final user-visible output.

### Checkpoint

- `planning.md` describes all three tools with exact inputs and return values.
- The planning loop describes specific conditional logic.
- The architecture diagram shows data/control flow and the error branch.
- The AI Tool Plan references specific spec sections.
- The walkthrough traces one complete example interaction.

## Milestone 3: Build and Test Each Tool in Isolation

⏰ ~2–3 hours

Implement the existing stubs in `tools.py`. Do not create separate files for each tool.

### `search_listings(description, size, max_price)`

- Use `load_listings()` from `utils/data_loader.py`.
- Do not re-implement file loading.
- Handle zero results with an empty list instead of an exception.

### `suggest_outfit(new_item, wardrobe)`

- Call Groq with `meta-llama/llama-4-scout-17b-16e-instruct`.
- Use `GROQ_API_KEY` from `.env`.
- Handle an empty wardrobe gracefully.

### `create_fit_card(outfit, new_item)`

- Call the LLM.
- Guard against an empty outfit string.
- Return an informative error string rather than crashing.
- Run multiple times and verify outputs vary; increase temperature if necessary.

### Tests

Create `tests/test_tools.py` with tests for success and failure modes.

Example:

```python
from tools import search_listings


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
```

Run tests with:

```bash
python -m pytest tests/
```

Use `python -m pytest`, not bare `pytest`, so imports such as `from tools import search_listings` resolve correctly.

### Checkpoint

Each tool works independently. Every required failure mode returns a specific informative response instead of raising an exception or returning nothing.

## Milestone 4: Wire Up the Planning Loop and State

⏰ ~2 hours

Open `agent.py`. The session dictionary structure and `run_agent()` signature should already exist in the starter repo.

Requirements:

- Implement `run_agent()` using the Planning Loop and State Management sections from `planning.md`.
- Branch on the result of `search_listings`.
- Store values in the session dictionary.
- Do not call all three tools unconditionally.
- Implement `handle_query()` in `app.py` so the Gradio interface calls `run_agent()` and maps session values into the output panels.
- Verify that `session["selected_item"]` is the same item passed to `suggest_outfit`.
- Verify that `session["outfit_suggestion"]` is the same value passed to `create_fit_card`.
- Verify the no-results path sets `session["error"]` and leaves `session["fit_card"]` as `None`.

### Checkpoint

A successful query flows through all three tools with state passed automatically. A failed search follows a different branch and stops before outfit generation.

## Milestone 5: Test Every Failure Mode Deliberately

⏰ ~1 hour

### Search failure

```bash
python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"
```

Expected: `[]` without an exception.

Then run the full agent with the same impossible query and confirm the user sees a useful suggestion for what to change.

### Empty wardrobe

```bash
python -c "
from tools import search_listings, suggest_outfit
from utils.data_loader import get_empty_wardrobe
results = search_listings('vintage graphic tee', size=None, max_price=50)
print(suggest_outfit(results[0], get_empty_wardrobe()))
"
```

Expected: useful general styling advice rather than an exception or empty string.

### Empty outfit

```bash
python -c "
from tools import search_listings, create_fit_card
results = search_listings('vintage graphic tee', size=None, max_price=50)
print(create_fit_card('', results[0]))
"
```

Expected: descriptive error message string rather than a Python exception.

Screenshot or record at least one triggered failure for the demo video.

### Checkpoint

All three failure modes produce specific and informative agent responses.

## Milestone 6: Document and Record

⏰ ~1–1.5 hours

Run the interface:

```bash
python app.py
```

Open the URL shown in the terminal and verify all three output panels work on a happy-path query.

### README requirements

The final README must include:

- Tool inventory with exact names, parameter names/types, outputs, and purpose.
- Planning loop explanation with conditional logic.
- State management approach: what is stored, when, and how it is passed.
- Error handling strategy for each tool, with at least one concrete tested example.
- Spec reflection: one way the spec helped and one way implementation diverged from it and why.
- AI usage section with at least 2 specific examples describing what you gave the AI tool, what it produced, and what you revised or overrode.

### Demo video requirements

Record a **3–5 minute** demo showing:

- One complete interaction using all 3 required tools.
- Narration explaining which tool is called and why.
- State visibly or verbally passing between tools.
- At least one triggered failure with graceful handling.

Link the video from the README.

## 📬 Submitting Your Project

Submit all of the following through the Course Portal:

- Link to your forked GitHub repository.
- `planning.md` in the repo root.
- `README.md` containing:
  - Tool inventory.
  - Planning loop explanation.
  - State management approach.
  - Error handling strategy with at least one concrete example.
  - Spec reflection.
  - AI usage section with at least 2 specific instances.
- 3–5 minute demo video linked from the README showing:
  - Complete multi-step interaction.
  - Narration of tool decisions.
  - State passing.
  - At least one triggered failure.
