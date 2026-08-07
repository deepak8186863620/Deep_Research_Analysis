"""
utils/text_utils.py

PURPOSE: Reusable text processing helpers shared across the whole app.
         Instead of duplicating these functions in every file that needs them,
         we define them once here and import from anywhere.
"""

import re
from typing import Any


def extract_text_from_message(content: Any) -> str:
    """
    PURPOSE: Safely pull plain text out of an AI message's content field.

    WHY NEEDED: Different LLM providers return content in different shapes:
      - Gemini returns a plain string.
      - Some providers (Anthropic, etc.) return a LIST of content blocks:
          [{"type": "text", "text": "..."}, {"type": "tool_use", ...}]
    This function handles both cases so the rest of the app never has to worry
    about which format the LLM returned.

    Args:
        content: The raw .content field from a LangChain BaseMessage.

    Returns:
        A clean plain-text string.
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        # Extract only the "text" type blocks, ignore tool_use and other blocks
        text_parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return "\n".join(text_parts) if text_parts else str(content)

    return str(content)


def truncate_text(text: str, max_chars: int = 500, suffix: str = "...") -> str:
    """
    PURPOSE: Safely shorten a long text to a maximum character limit.

    WHY NEEDED: When logging errors or storing previews in MongoDB, we don't
    want to accidentally store a 50,000 character paper abstract. This prevents
    oversized documents and keeps previews readable.

    Args:
        text:      The text to potentially truncate.
        max_chars: Maximum number of characters to allow.
        suffix:    String appended when text is cut (default "...").

    Returns:
        Original text if short enough, otherwise truncated text + suffix.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars - len(suffix)] + suffix


def clean_whitespace(text: str) -> str:
    """
    PURPOSE: Normalize whitespace in text fetched from APIs or parsed from HTML.

    WHY NEEDED: Semantic Scholar abstracts and Tavily results often contain
    extra newlines, tabs, or multiple spaces. This makes them cleaner before
    chunking and embedding so FAISS gets better quality vectors.

    Example:
        "  Deep   learning\\n\\n\\n is powerful  " → "Deep learning is powerful"
    """
    # Replace any sequence of whitespace (tabs, newlines, multiple spaces) with a single space
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def format_paper_citation(title: str, year: Any, citations: int) -> str:
    """
    PURPOSE: Produce a consistently formatted citation string for academic papers.

    WHY NEEDED: Papers are displayed in the final research report with their
    citation count as a trust indicator. Centralizing the format here ensures
    every part of the app shows citations the same way.

    Example output: "[Attention Is All You Need, 2017 — 80,432 citations]"
    """
    return f"[{title}, {year} — {citations:,} citations]"
