"""
ranker.py
=========
Multi-signal ranking algorithm for the Deep Research pipeline.

HOW TO USE THIS FILE:
  1. The 3 scoring helpers below (citation, recency, authority) are already
     written for you — read them, understand them, then test them.
  2. You need to implement:
       - relevance_scores()  ← the ML cross-encoder part
       - rank_papers()       ← combines all 4 signals into a final ranked list
       - rank_web_results()  ← same idea but for Tavily web results

WHERE THIS PLUGS IN:
  deep_research_agent.py → after _fetch_tavily_multi() returns,
  before Phase 2 (fetching web pages). Import rank_papers and call it.

SIGNAL WEIGHTS (must sum to 1.0):
  Relevance  50%  — does this paper actually answer the query?
  Citation   25%  — how much has the field trusted this paper?
  Recency    15%  — is this recent research?
  Authority  10%  — peer-reviewed vs preprint vs web page?
"""

import math
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

CURRENT_YEAR: int = datetime.now().year

# Weights for the final score — feel free to experiment with these
W_RELEVANCE  = 0.50
W_CITATION   = 0.25
W_RECENCY    = 0.15
W_AUTHORITY  = 0.10

# How authoritative is each source type by default?
# Semantic Scholar papers are peer-reviewed and citation-verified.
# arXiv papers are preprints — solid research but not yet peer-reviewed.
# Web pages are unknown quality — could be a blog or a university study.
AUTHORITY_MAP: Dict[str, float] = {
    "Semantic Scholar": 1.0,
    "arXiv":            0.7,
    "web":              0.4,
}

# Cross-encoder model name — downloaded once and cached by HuggingFace
# This model was trained on MS-MARCO (millions of web search relevance labels)
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


# ─────────────────────────────────────────────────────────────────────────────
# SIGNAL 1 — CITATION IMPACT SCORE
# ─────────────────────────────────────────────────────────────────────────────

def citation_score(citations: int, max_citations: int) -> float:
    """
    Returns a value between 0.0 and 1.0 representing how impactful this
    paper is relative to the most-cited paper in the current result set.

    WHY LOG NORMALIZATION?
    Citation counts follow a power-law distribution (a few papers have
    tens of thousands, most have hundreds). Without log, a paper with
    50,000 citations is 100x "better" than one with 500 citations.
    With log:
        log10(50000 + 1) ≈ 4.70
        log10(500   + 1) ≈ 2.70
    So it's only 1.7x different — much fairer for the final score.

    Args:
        citations:     The citation count of this specific paper.
        max_citations: The highest citation count among all papers being ranked.
                       Used as the denominator to normalize to [0, 1].

    Returns:
        0.0  → paper has 0 citations
        1.0  → paper has the most citations of the entire result set
        0.57 → example: 500 citations when max is 50,000
    """
    if max_citations <= 0:
        return 0.0

    numerator   = math.log10(citations + 1)       # +1 avoids log10(0) = undefined
    denominator = math.log10(max_citations + 1)   # normalise against the max

    return numerator / denominator


# ─────────────────────────────────────────────────────────────────────────────
# SIGNAL 2 — RECENCY SCORE
# ─────────────────────────────────────────────────────────────────────────────

def recency_score(year: Any) -> float:
    """
    Returns a value between 0.0 and 1.0 based on how recent the paper is.

    A paper from the current year scores 1.0.
    A paper 10+ years old scores 0.0.
    The decay is LINEAR between those two points.

    WHY 10-YEAR WINDOW?
    In most scientific fields, research older than 10 years is either
    superseded by newer work or still foundational (which the citation
    signal already rewards). Recency is just a tiebreaker.

    Args:
        year: The publication year. Can be an int, string, or None.
              If it can't be parsed, returns 0.5 (neutral — don't punish
              a paper just because its year is missing from the API).

    Returns:
        1.0  → published this year (age = 0)
        0.5  → published 5 years ago
        0.1  → published 9 years ago
        0.0  → published 10+ years ago (clamped at 0, never negative)
        0.5  → year unknown
    """
    try:
        age = CURRENT_YEAR - int(year)
        return max(0.0, 1.0 - age / 10.0)
    except (ValueError, TypeError):
        return 0.5   # Unknown year — neutral score, don't penalise


# ─────────────────────────────────────────────────────────────────────────────
# SIGNAL 3 — SOURCE AUTHORITY SCORE
# ─────────────────────────────────────────────────────────────────────────────

def authority_score(source: str) -> float:
    """
    Returns a fixed authority score based on where the source came from.

    This is the simplest signal — just a dictionary lookup.
    It encodes domain knowledge: peer-reviewed sources are inherently
    more reliable than anonymous web pages, all else being equal.

    Args:
        source: One of "Semantic Scholar", "arXiv", or "web".
                Any unknown source defaults to web quality (0.4).

    Returns:
        1.0  → Semantic Scholar (peer-reviewed)
        0.7  → arXiv (preprint, rigorous but unreviewed)
        0.4  → Web page (unknown quality)
    """
    return AUTHORITY_MAP.get(source, 0.4)   # default: web-level authority


# ─────────────────────────────────────────────────────────────────────────────
# CROSS-ENCODER MODEL LOADER
# ─────────────────────────────────────────────────────────────────────────────

# This is a module-level variable — starts as None, gets filled on first use.
# Python keeps module globals alive for the entire process lifetime, so the
# model loads once (~90MB) and stays in memory for all subsequent requests.
_cross_encoder = None


def _load_model():
    """
    Lazy singleton loader for the CrossEncoder model.

    WHAT IS A CROSS-ENCODER?
    Unlike a bi-encoder (which encodes query and document separately),
    a cross-encoder reads the query AND the document together in one
    forward pass through a transformer. This means "caffeine" in the
    query can directly attend to "adenosine" in the abstract —
    producing a much more accurate relevance signal.

    The model is downloaded from HuggingFace on the FIRST call and
    cached in ~/.cache/huggingface/ so subsequent starts are instant.

    Returns:
        A loaded CrossEncoder instance ready for .predict() calls.
    """
    global _cross_encoder

    if _cross_encoder is None:
        # Import here so the module loads even if sentence-transformers
        # is not installed — you'll only hit this error when you actually
        # call a ranking function, not at import time.
        from sentence_transformers import CrossEncoder

        logger.info(f"Loading CrossEncoder: {CROSS_ENCODER_MODEL}")
        _cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL, max_length=512)
        logger.info("CrossEncoder loaded.")

    return _cross_encoder


# ─────────────────────────────────────────────────────────────────────────────
# YOUR TURN — IMPLEMENT THESE
# ─────────────────────────────────────────────────────────────────────────────

def relevance_scores(query: str, documents: List[str]) -> List[float]:
    """
    Use the cross-encoder to score how relevant each document is to the query.

    The model returns raw logits (can be negative, no fixed range).
    You need to normalize them to [0, 1] using min-max scaling so they
    can be combined with the other signals fairly.

    MIN-MAX FORMULA:
        normalized = (score - min_score) / (max_score - min_score)

    EDGE CASE: What if all scores are identical? (max == min)
        Division by zero → return [0.5] * len(documents) instead.

    Steps to implement:
        1. Call _load_model() to get the cross-encoder instance
        2. Build pairs: [(query, doc) for doc in documents]
        3. Call model.predict(pairs) → returns a numpy array of floats
        4. Convert to a Python list with .tolist()
        5. Find min and max of the list
        6. Apply min-max normalization
        7. Return the normalized list

    Args:
        query:     The user's research topic (e.g. "effects of caffeine on sleep")
        documents: List of strings — one per paper (title + first 400 chars of abstract)

    Returns:
        List of floats in [0.0, 1.0], same length and same order as documents.
        Index 0 in the return corresponds to documents[0].
    """
    # TODO: implement this
    raise NotImplementedError("You need to implement relevance_scores()")


def rank_papers(
    query:  str,
    papers: List[Dict],
    top_k:  int = 10,
) -> List[Dict]:
    """
    Main ranking function — combines all 4 signals and returns the top_k papers.

    HOW IT WORKS:
        1. Build a document string per paper: title + abstract[:400]
        2. Get relevance scores for all papers in one batch call
        3. Find max_citations across all papers (needed for normalization)
        4. For each paper:
               rel  = relevance_scores output for this paper  (0–1)
               cit  = citation_score(paper citations, max_citations)
               rec  = recency_score(paper year)
               auth = authority_score(paper source)
               paper["_score"] = W_RELEVANCE*rel + W_CITATION*cit
                                + W_RECENCY*rec  + W_AUTHORITY*auth
        5. Sort papers descending by "_score"
        6. Return papers[:top_k]

    Hint — paper dict keys to use:
        p.get("title", "")
        p.get("abstract", "")[:400]
        p.get("citations", 0) or 0    ← 'or 0' handles None from API
        p.get("year")
        p.get("source", "web")

    Args:
        query:  The user's research query string.
        papers: List of paper dicts (already filtered — no "error" keys).
        top_k:  How many papers to return after ranking.

    Returns:
        Top-K paper dicts, sorted best-first. Each dict will have a
        new "_score" key added (float in [0, 1]) so callers can see the score.
    """
    # TODO: implement this
    raise NotImplementedError("You need to implement rank_papers()")
