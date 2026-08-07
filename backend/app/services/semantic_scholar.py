"""
services/semantic_scholar.py

PURPOSE: A dedicated service layer for all Semantic Scholar API interactions.

WHY A SEPARATE FILE FROM research_agent.py?
  The research agent should only handle the AI decision-making loop.
  All the details of HOW to call an external API (URL, params, retries,
  error handling, rate limits) belong in a service layer.
  This makes the code testable: you can test this service independently
  without running the entire LangGraph agent.

WHAT THIS SERVICE DOES:
  1. search_papers()      → finds top N papers by keyword
  2. fetch_full_text()    → tries to get the FULL paper text (not just abstract)
                            via arXiv when the paper is on arXiv
  3. get_paper_details()  → fetches detailed metadata for a single paper by ID
  4. get_references()     → fetches the list of papers that a paper cites
                            (used for "citation chaining" — a deep research technique)
"""

import time
import logging
import arxiv
import requests
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Semantic Scholar base URL — no API key required for basic usage
# With a free API key you get higher rate limits (register at semanticscholar.org)
SEMANTIC_SCHOLAR_BASE = "https://api.semanticscholar.org/graph/v1"

# Be a good API citizen: wait between requests to avoid hitting rate limits
# The free tier allows ~100 requests per 5 minutes (about 1 per 3 seconds)
REQUEST_DELAY_SECONDS = 1.0


def _get(endpoint: str, params: dict, timeout: int = 15) -> Optional[dict]:
    """
    PURPOSE: Centralized HTTP GET helper for all Semantic Scholar calls.

    WHY CENTRALIZE THIS?
    - One place to handle rate limiting (REQUEST_DELAY_SECONDS)
    - One place to handle timeouts and errors
    - If Semantic Scholar ever changes their auth or base URL, we fix it once here

    Args:
        endpoint: API path after the base URL (e.g. "/paper/search")
        params:   Query parameters dict
        timeout:  Max seconds to wait for response

    Returns:
        Parsed JSON dict on success, None on failure.
    """
    url = f"{SEMANTIC_SCHOLAR_BASE}{endpoint}"
    
    headers = {}
    if settings.SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = settings.SEMANTIC_SCHOLAR_API_KEY

    try:
        # Small delay to respect rate limits ONLY if we don't have an API key
        if not settings.SEMANTIC_SCHOLAR_API_KEY:
            time.sleep(REQUEST_DELAY_SECONDS)

        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.Timeout:
        logger.warning(f"Semantic Scholar request timed out: {url}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.warning(f"Semantic Scholar HTTP error {e.response.status_code}: {url}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error calling Semantic Scholar: {e}")
        return None


def search_papers(query: str, limit: int = 10) -> list[dict]:
    """
    PURPOSE: Search Semantic Scholar for academic papers matching a query.

    Returns papers sorted by citation count (descending) so the most
    authoritative, peer-validated papers appear first.

    We request these fields:
    - title, year, abstract   → core content
    - citationCount           → trust indicator (more citations = more trusted)
    - externalIds             → contains 'ArXiv' ID if paper is on arXiv
    - openAccessPdf           → direct PDF URL if paper is freely available

    Args:
        query: Search query string (e.g. "transformer architecture NLP")
        limit: How many papers to return (default 10)

    Returns:
        List of paper dicts, sorted by citation count descending.
        Empty list if search fails.
    """
    data = _get(
        "/paper/search",
        params={
            "query": query,
            "fields": "title,authors,year,abstract,citationCount,externalIds,openAccessPdf",
            "limit": limit,
        },
    )

    if not data:
        return []

    papers = data.get("data", [])

    # Sort by citation count — most cited = most peer-reviewed and trusted
    papers.sort(key=lambda p: p.get("citationCount") or 0, reverse=True)

    logger.info(f"Semantic Scholar: found {len(papers)} papers for '{query}'")
    return papers


def fetch_full_text(paper: dict) -> Optional[str]:
    """
    PURPOSE: Try to fetch the FULL TEXT of a paper, not just the abstract.

    WHY FULL TEXT?
    - Abstracts are ~300 words. Full papers are 5,000–15,000 words.
    - Full text has methods, results, tables, conclusions — the real details.
    - FAISS can index these details and the agent can answer very specific questions.

    HOW IT WORKS (in order of preference):
    1. Check if the paper has an arXiv ID in externalIds
       → If yes, use the `arxiv` Python package to download the paper summary
         (arxiv package gives us full metadata + abstract, not the PDF text directly)
    2. Check if openAccessPdf URL exists
       → If yes, we log it (PDF parsing requires extra libraries like pypdf —
         we leave this as a future enhancement)
    3. Fall back to the abstract from the paper dict

    Args:
        paper: A paper dict from search_papers()

    Returns:
        The best available text for this paper (full text > abstract > None)
    """
    # ── Strategy 1: Try arXiv ────────────────────────────────────────────────
    external_ids = paper.get("externalIds") or {}
    arxiv_id = external_ids.get("ArXiv")

    if arxiv_id:
        try:
            logger.info(f"Fetching full paper from arXiv: {arxiv_id}")

            # arxiv.Search fetches paper metadata from arXiv API
            # It gives us a richer, longer summary than Semantic Scholar's abstract
            search = arxiv.Search(id_list=[arxiv_id])
            arxiv_paper = next(arxiv.Client().results(search), None)

            if arxiv_paper:
                # arXiv gives us: title, summary (extended abstract), categories,
                # authors, published date — all very useful for research
                full_text = (
                    f"Title: {arxiv_paper.title}\n"
                    f"Authors: {', '.join(str(a) for a in arxiv_paper.authors)}\n"
                    f"Published: {arxiv_paper.published.strftime('%Y-%m-%d') if arxiv_paper.published else 'N/A'}\n"
                    f"Categories: {', '.join(arxiv_paper.categories)}\n\n"
                    f"Summary:\n{arxiv_paper.summary}"
                )
                logger.info(f"Successfully fetched arXiv paper: {arxiv_id}")
                return full_text

        except Exception as e:
            logger.warning(f"Failed to fetch arXiv paper {arxiv_id}: {e}")

    # ── Strategy 2: Log open access PDF URL (for future enhancement) ─────────
    open_access = paper.get("openAccessPdf")
    if open_access and open_access.get("url"):
        pdf_url = open_access["url"]
        logger.info(f"Open access PDF available (not parsed): {pdf_url}")
        # Future enhancement: download + parse PDF with pypdf
        # For now, we fall through to the abstract

    # ── Strategy 3: Fall back to abstract ────────────────────────────────────
    abstract = paper.get("abstract")
    if abstract:
        logger.info(f"Using abstract fallback for paper: {paper.get('title', 'Unknown')}")
        return abstract

    return None


def get_paper_details(paper_id: str) -> Optional[dict]:
    """
    PURPOSE: Fetch full metadata for a specific paper by its Semantic Scholar paper ID.

    WHY NEEDED?
    The search endpoint returns a summary. This endpoint gets deeper fields like:
    - Full author list with affiliations
    - All referenced papers (what this paper cites)
    - All citing papers (who cited this paper)
    - TLDR summary (Semantic Scholar's AI-generated one-line summary)

    Args:
        paper_id: Semantic Scholar paper ID (from search results)

    Returns:
        Full paper detail dict, or None on failure.
    """
    return _get(
        f"/paper/{paper_id}",
        params={
            "fields": "title,authors,year,abstract,citationCount,tldr,references,externalIds"
        },
    )


def get_references(paper_id: str, limit: int = 5) -> list[dict]:
    """
    PURPOSE: Get the papers that a given paper cites (its reference list).

    WHY IS THIS USEFUL?
    This is called "citation chaining" — a key deep research technique.

    Example:
      User asks about "transformers in NLP"
      Agent finds "Attention Is All You Need" (2017)
      Agent then fetches ITS references → finds the papers that inspired transformers
      This gives a complete historical picture, not just the top-level result.

    Args:
        paper_id: Semantic Scholar paper ID
        limit:    How many references to return

    Returns:
        List of reference paper dicts, empty list on failure.
    """
    data = _get(
        f"/paper/{paper_id}/references",
        params={
            "fields": "title,year,abstract,citationCount",
            "limit": limit,
        },
    )

    if not data:
        return []

    # Each item has a "citedPaper" key containing the actual paper data
    refs = [item.get("citedPaper", {}) for item in data.get("data", [])]

    # Filter out refs with no abstract (not useful for FAISS indexing)
    refs = [r for r in refs if r.get("abstract")]

    logger.info(f"Fetched {len(refs)} references for paper {paper_id}")
    return refs
