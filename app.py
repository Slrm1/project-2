"""
app.py

Gradio interface for FitFindr.

Run with:
    python app.py
"""

import gradio as gr

from agent import run_agent
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


# ── query handler ─────────────────────────────────────────────────────────────

def handle_query(user_query: str, wardrobe_choice: str) -> tuple[str, str, str]:
    """Run FitFindr and map session state to the three output panels."""
    if not isinstance(user_query, str) or not user_query.strip():
        return "Please describe what you're looking for.", "", ""

    if wardrobe_choice == "Empty wardrobe (new user)":
        wardrobe = get_empty_wardrobe()
    else:
        wardrobe = get_example_wardrobe()

    session = run_agent(user_query.strip(), wardrobe)

    if session.get("error"):
        adjustment_text = ""
        if session.get("adjustments"):
            adjustment_text = "\n\nWhat I tried:\n- " + "\n- ".join(session["adjustments"])
        return session["error"] + adjustment_text, "", ""

    item = session["selected_item"]
    listing_lines = [
        f"{item.get('title', 'Untitled listing')}",
        f"Price: ${float(item.get('price', 0)):.2f}",
        f"Platform: {item.get('platform', 'unknown')}",
        f"Size: {item.get('size', 'unknown')}",
        f"Condition: {item.get('condition', 'unknown')}",
    ]

    if item.get("brand"):
        listing_lines.append(f"Brand: {item['brand']}")
    if item.get("colors"):
        listing_lines.append(f"Colors: {', '.join(item['colors'])}")
    if item.get("style_tags"):
        listing_lines.append(f"Style: {', '.join(item['style_tags'])}")

    if session.get("adjustments"):
        listing_lines.append("\nSearch adjustment(s):")
        listing_lines.extend(f"- {message}" for message in session["adjustments"])

    listing_text = "\n".join(listing_lines)
    return (
        listing_text,
        session.get("outfit_suggestion") or "",
        session.get("fit_card") or "",
    )


# ── interface ─────────────────────────────────────────────────────────────────

EXAMPLE_QUERIES = [
    "vintage graphic tee under $30",
    "90s track jacket in size M",
    "flowy midi skirt under $40",
    "black combat boots size 8",
    "designer ballgown size XXS under $5",   # deliberate no-results test
]


def build_interface():
    with gr.Blocks(title="FitFindr") as demo:
        gr.Markdown("""
# FitFindr 🛍️
Find secondhand pieces and get outfit ideas based on your wardrobe.
Describe what you're looking for — include size and price if you want to filter.
        """)

        with gr.Row():
            query_input = gr.Textbox(
                label="What are you looking for?",
                placeholder="e.g. vintage graphic tee under $30, size M",
                lines=2,
                scale=3,
            )
            wardrobe_choice = gr.Radio(
                choices=["Example wardrobe", "Empty wardrobe (new user)"],
                value="Example wardrobe",
                label="Wardrobe",
                scale=1,
            )

        submit_btn = gr.Button("Find it", variant="primary")

        with gr.Row():
            listing_output = gr.Textbox(
                label="🛍️ Top listing found",
                lines=8,
                interactive=False,
            )
            outfit_output = gr.Textbox(
                label="👗 Outfit idea",
                lines=8,
                interactive=False,
            )
            fitcard_output = gr.Textbox(
                label="✨ Your fit card",
                lines=8,
                interactive=False,
            )

        gr.Examples(
            examples=[[q, "Example wardrobe"] for q in EXAMPLE_QUERIES],
            inputs=[query_input, wardrobe_choice],
            label="Try these queries",
        )

        submit_btn.click(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[listing_output, outfit_output, fitcard_output],
        )
        query_input.submit(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[listing_output, outfit_output, fitcard_output],
        )

    return demo


if __name__ == "__main__":
    demo = build_interface()
    demo.launch()
