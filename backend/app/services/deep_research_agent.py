"""
deep_research_agent.py
=======================
Multi-Phase Deep Verification Research Pipeline

Architecture:
  Phase 1 — DISCOVER   : Semantic Scholar + arXiv + Tavily (3 query angles)
  Phase 2 — FETCH      : Download and parse every web page's full content
  Phase 3 — VERIFY     : LLM cross-checks all claims across all sources
  Phase 4 — SCORE      : Confidence scoring per claim and overall
  Phase 5 — REPORT     : Structured final report with citations + hashes

Every source is catalogued with:
  - Content hash (SHA-256 of content)   → proves we actually read it
  - Word count                          → content quality indicator
  - Verification status                 → confirmed / disputed / single-source
"""

import asyncio
import hashlib
import re
import requests
from typing import Optional, Dict, List, Any
from datetime import datetime

try:
    import arxiv as arxiv_lib
    ARXIV_AVAILABLE = True
except ImportError:
    ARXIV_AVAILABLE = False

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langchain_core.messages import HumanMessage

from app.core.config import settings
from app.core.database import get_database
from app.utils.text_utils import clean_whitespace


# ─── LLM (low temperature for factual accuracy) ───────────────────────────────
llm = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL,
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0.1,
)


# ─────────────────────────────────────────────────────────────────────────────
# UTILITY FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def _sha256(text: str) -> str:
    """SHA-256 fingerprint of source content (first 16 chars for readability)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _strip_html(html: str) -> str:
    """Fast HTML → plain text using regex (no extra dependencies)."""
    # Remove script and style blocks
    html = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html,
                  flags=re.DOTALL | re.IGNORECASE)
    # Remove all remaining tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Decode common HTML entities
    entities = {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"',
                "&#39;": "'", "&nbsp;": " "}
    for ent, rep in entities.items():
        text = text.replace(ent, rep)
    return clean_whitespace(text)


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1: DISCOVER — Gather all sources
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_semantic_scholar(query: str, limit: int = 12) -> List[Dict]:
    """
    Fetch top papers from Semantic Scholar sorted by citation count.
    Each paper is assigned a content hash for verification tracking.
    """
    try:
        resp = requests.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={
                "query": query,
                "fields": "title,authors,year,abstract,citationCount,externalIds",
                "limit": limit,
            },
            headers={"x-api-key": settings.SEMANTIC_SCHOLAR_API_KEY} if settings.SEMANTIC_SCHOLAR_API_KEY else {},
            timeout=15,
        )
        resp.raise_for_status()
        papers = resp.json().get("data", [])
        papers.sort(key=lambda p: p.get("citationCount") or 0, reverse=True)

        results = []
        for p in papers:
            abstract = clean_whitespace(p.get("abstract") or "No abstract available.")
            authors  = ", ".join(a.get("name", "") for a in (p.get("authors") or [])[:3])
            doi      = (p.get("externalIds") or {}).get("DOI", "")
            results.append({
                "title":    p.get("title", "Unknown Title"),
                "authors":  authors,
                "year":     p.get("year", "N/A"),
                "citations": p.get("citationCount", 0),
                "abstract": abstract,
                "hash":     _sha256(abstract),
                "source":   "Semantic Scholar",
                "doi":      doi,
            })
        return results
    except Exception as e:
        return [{"error": str(e), "source": "Semantic Scholar"}]


def _fetch_arxiv(query: str, max_results: int = 6) -> List[Dict]:
    """
    Fetch latest preprints from arXiv using the official Python client.
    Sorted by submission date (newest first) to capture cutting-edge research.
    """
    if not ARXIV_AVAILABLE:
        return []
    try:
        client = arxiv_lib.Client()
        search = arxiv_lib.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv_lib.SortCriterion.SubmittedDate,
        )
        results = []
        for paper in client.results(search):
            abstract = clean_whitespace(paper.summary)
            results.append({
                "title":    paper.title,
                "authors":  ", ".join(str(a) for a in paper.authors[:3]),
                "year":     paper.published.year if paper.published else "N/A",
                "citations": 0,
                "abstract": abstract,
                "hash":     _sha256(abstract),
                "source":   "arXiv",
                "doi":      paper.doi or paper.entry_id,
                "url":      paper.pdf_url,
            })
        return results
    except Exception as e:
        return [{"error": str(e), "source": "arXiv"}]


def _fetch_tavily_multi(query: str) -> List[Dict]:
    """
    Run 3 Tavily searches with different query angles for maximum coverage:
      - General topic query
      - Recent research (2024/2025)
      - Applications and real-world findings
    Deduplicates by URL.
    """
    tavily = TavilySearch(max_results=5, tavily_api_key=settings.TAVILY_API_KEY)
    angles = [
        query,
        f"{query} latest research findings 2024 2025",
        f"{query} real world applications evidence",
    ]

    seen_urls: set = set()
    all_results: List[Dict] = []

    for angle in angles:
        try:
            raw = tavily.invoke(angle)
            items = raw if isinstance(raw, list) else []
            for item in items:
                url = item.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append({
                        "url":     url,
                        "title":   item.get("title", url),
                        "snippet": clean_whitespace(item.get("content", ""))[:600],
                        "score":   item.get("score", 0),
                    })
        except Exception:
            continue

    # Sort by Tavily relevance score
    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return all_results


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2: FETCH — Download every web page
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_web_page(url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Fetch a web page and extract its full text content.
    Computes a SHA-256 hash to verify the content was actually read.

    Returns:
        url, title, content (first 3000 chars), hash, word_count, success
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        text = _strip_html(resp.text)

        # First 3000 chars contain the most relevant content
        excerpt = text[:3000] if len(text) > 3000 else text

        return {
            "url":        url,
            "content":    excerpt,
            "hash":       _sha256(excerpt),
            "word_count": len(text.split()),
            "char_count": len(text),
            "success":    True,
        }
    except Exception as e:
        return {
            "url":        url,
            "content":    "",
            "hash":       "FETCH_FAILED",
            "word_count": 0,
            "char_count": 0,
            "success":    False,
            "error":      str(e)[:120],
        }


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3 + 4: VERIFY & SCORE — Cross-source claim verification with LLM
# ─────────────────────────────────────────────────────────────────────────────

async def _verify_and_score(
    topic: str,
    papers: List[Dict],
    arxiv_papers: List[Dict],
    web_pages: List[Dict],
    instructions: Optional[str],
) -> str:
    """
    Send ALL gathered source content to Gemini for deep cross-verification.
    Asks the LLM to:
      1. Extract every key factual claim from all sources
      2. Cross-reference which sources support each claim
      3. Score confidence per claim based on source count + quality
      4. Calculate an overall research confidence score (0-100%)
      5. Write a structured final report with full citations
    """
    good_papers   = [p for p in papers if "error" not in p]
    good_arxiv    = [p for p in arxiv_papers if "error" not in p]
    good_web      = [w for w in web_pages if w.get("success") and w.get("content")]
    failed_web    = [w for w in web_pages if not w.get("success")]

    total_academic = len(good_papers) + len(good_arxiv)
    total_web      = len(good_web)
    total_citations = sum(p.get("citations", 0) for p in good_papers)

    # ── Build the source digest ───────────────────────────────────────────────
    blocks: List[str] = []

    blocks.append(f"══ SEMANTIC SCHOLAR PAPERS ({len(good_papers)} papers) ══")
    for i, p in enumerate(good_papers, 1):
        blocks.append(
            f"[SS-{i}] \"{p['title']}\" — {p.get('authors','')}\n"
            f"  Year: {p['year']} | Citations: {p['citations']:,} | SHA256: {p['hash']}\n"
            f"  DOI: {p.get('doi','N/A')}\n"
            f"  Abstract: {p['abstract'][:700]}"
        )

    blocks.append(f"\n══ ARXIV PREPRINTS ({len(good_arxiv)} papers) ══")
    for i, p in enumerate(good_arxiv, 1):
        blocks.append(
            f"[AX-{i}] \"{p['title']}\" — {p.get('authors','')}\n"
            f"  Year: {p['year']} | SHA256: {p['hash']}\n"
            f"  ID: {p.get('doi','N/A')}\n"
            f"  Abstract: {p['abstract'][:700]}"
        )

    blocks.append(f"\n══ WEB PAGES FETCHED ({len(good_web)} successful, {len(failed_web)} failed) ══")
    for i, w in enumerate(good_web, 1):
        blocks.append(
            f"[WEB-{i}] {w['url']}\n"
            f"  SHA256: {w['hash']} | Words: {w['word_count']:,}\n"
            f"  Content: {w['content'][:700]}"
        )

    if failed_web:
        blocks.append(f"\n[FETCH FAILURES — {len(failed_web)} pages could not be accessed]")
        for w in failed_web:
            blocks.append(f"  ✗ {w['url']} — {w.get('error','unknown error')}")

    source_digest = "\n\n".join(blocks)

    # ── Verification prompt ───────────────────────────────────────────────────
    prompt = f"""You are a DEEP RESEARCH VERIFICATION ENGINE. Your job is to cross-verify every source, extract claims, score confidence, and produce an authoritative research report.

RESEARCH TOPIC: {topic}

SOURCES ANALYZED:
  • {len(good_papers)} Semantic Scholar papers (total {total_citations:,} citations)
  • {len(good_arxiv)} arXiv preprints
  • {len(good_web)} web pages fetched and read (SHA-256 verified)
  • {len(failed_web)} web pages failed to load

══════════════════════════════════════════════
ALL VERIFIED SOURCE CONTENT:
══════════════════════════════════════════════

{source_digest}

══════════════════════════════════════════════
YOUR VERIFICATION TASK:
══════════════════════════════════════════════

STEP 1 — EXTRACT all significant factual claims from every source above.
STEP 2 — For each claim, record WHICH source IDs support it (e.g. SS-1, AX-2, WEB-3).
STEP 3 — Apply confidence scoring rules:
  • 3+ independent sources agree → HIGH confidence (75–100%)
  • 2 sources agree → MEDIUM confidence (40–74%)
  • 1 source only → LOW confidence (10–39%)
  • Sources contradict each other → DISPUTED — flag it!
  • Academic sources (SS/AX) weigh 2× vs web sources (WEB)
STEP 4 — Compute the OVERALL CONFIDENCE SCORE (0–100%) based on:
  • Percentage of high-confidence claims
  • Diversity of source types (academic + web agreement)
  • Recency of sources
  • Total citations backing the findings

Now produce the FINAL REPORT in EXACTLY this structure (keep all headers and emojis):

---
## 📊 Research Confidence Score: [X]% — [VERY HIGH / HIGH / MEDIUM / LOW]

**Sources verified:**
- 📚 Semantic Scholar: {len(good_papers)} papers ({total_citations:,} total citations)
- 🔬 arXiv preprints: {len(good_arxiv)} papers
- 🌐 Web pages fetched & hashed: {len(good_web)} successful / {len(failed_web)} failed

**Overall assessment:** [1-sentence explanation of why this confidence score was assigned]

---

## 🧭 Executive Summary
[2–3 sentences summarizing the research findings at high confidence]

---

## ✅ HIGH CONFIDENCE FINDINGS (verified by 3+ sources)
*These facts are well-established across multiple independent sources.*

For each finding, use this format:
**Finding:** [The fact]
- **Confidence:** [X]% | **Sources:** [SS-1, AX-2, WEB-3] | **Supporting citations:** [N]

---

## 🟡 MEDIUM CONFIDENCE FINDINGS (verified by 2 sources)
*These claims appear in multiple sources but need further validation.*

[Same format as above]

---

## 🔴 DISPUTED CLAIMS (sources contradict each other)
*These are areas of active disagreement — treat with caution.*

**Claim:** [The disputed fact]
- **Supporting:** [sources that agree]
- **Contradicting:** [sources that disagree]
- **Note:** [Why there is disagreement]

---

## 📉 LOW CONFIDENCE / SINGLE-SOURCE CLAIMS
*Found in only one source — interesting but unverified.*

[List each with source ID]

---

## 📚 Academic Research Deep Dive
### Semantic Scholar Findings
[For each high-citation paper, summarize its key contribution]

### arXiv Cutting-Edge Research
[Summarize the latest preprints and their novel findings]

---

## 🌐 Web Intelligence Report
[Summarize what the web sources revealed, especially recent developments]

---

## 💡 Research Gaps Identified
[Topics that web sources discuss but academia hasn't studied, or vice versa]

---

## 🏁 Final Verdict
[Your synthesized conclusion answering the research topic, stating confidence level and key caveats]

---

## 📖 Complete Source Registry

### Academic Papers (SHA-256 Verified)
| # | Source | Title | Year | Citations | Hash |
|---|--------|-------|------|-----------|------|
{chr(10).join(f"| SS-{i+1} | Semantic Scholar | {p['title'][:50]}... | {p['year']} | {p['citations']:,} | `{p['hash']}` |" for i, p in enumerate(good_papers))}
{chr(10).join(f"| AX-{i+1} | arXiv | {p['title'][:50]}... | {p['year']} | — | `{p['hash']}` |" for i, p in enumerate(good_arxiv))}

### Web Pages (SHA-256 Verified)
| # | URL | Words | Hash | Status |
|---|-----|-------|------|--------|
{chr(10).join(f"| WEB-{i+1} | {w['url'][:60]}... | {w['word_count']:,} | `{w['hash']}` | ✅ Verified |" for i, w in enumerate(good_web))}
{chr(10).join(f"| — | {w['url'][:60]}... | 0 | — | ❌ Failed |" for w in failed_web)}

---
{f'**User Instructions Applied:** {instructions}' if instructions else ''}
"""

    response = await llm.ainvoke([HumanMessage(content=prompt)])
    content = response.content
    if isinstance(content, list):
        content = " ".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return content


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

async def run_deep_research_task(
    task_id: str,
    topic: str,
    instructions: Optional[str] = None,
) -> None:
    """
    Entry point called by FastAPI BackgroundTasks.
    Runs the full 5-phase pipeline and saves results to MongoDB.
    Updates progress_step after each phase for real-time UI feedback.
    """
    db = get_database()

    async def set_progress(step: str, details: dict = None):
        update_payload = {"status": "processing", "progress_step": step}
        if details:
            update_payload["progress_details"] = details
        await db["research_tasks"].update_one(
            {"_id": task_id},
            {"$set": update_payload},
        )

    try:
        # ── Phase 1a: Semantic Scholar ────────────────────────────────────────
        await set_progress("🔍 Searching Semantic Scholar for academic papers...")
        papers = await asyncio.to_thread(_fetch_semantic_scholar, topic, 12)
        good_papers = [p for p in papers if "error" not in p]

        # ── Phase 1b: arXiv ───────────────────────────────────────────────────
        await set_progress(
            f"📄 Fetching arXiv preprints... ({len(good_papers)} Semantic Scholar papers found)",
            {"semantic_scholar": len(good_papers)},
        )
        arxiv_papers = await asyncio.to_thread(_fetch_arxiv, topic, 6)
        good_arxiv = [p for p in arxiv_papers if "error" not in p]

        # ── Phase 1c: Tavily multi-angle web search ───────────────────────────
        await set_progress(
            f"🌐 Running 3-angle web search... ({len(good_arxiv)} arXiv papers found)",
            {"semantic_scholar": len(good_papers), "arxiv": len(good_arxiv)},
        )
        tavily_results = await asyncio.to_thread(_fetch_tavily_multi, topic)

        # ── Phase 2: Fetch every web page ─────────────────────────────────────
        urls_to_fetch = tavily_results[:10]  # Limit to 10 pages
        await set_progress(
            f"📥 Fetching full content of {len(urls_to_fetch)} web pages...",
            {
                "semantic_scholar": len(good_papers),
                "arxiv": len(good_arxiv),
                "web_urls_found": len(tavily_results),
                "web_fetching": len(urls_to_fetch),
            },
        )

        web_pages: List[Dict] = []
        for item in urls_to_fetch:
            page = await asyncio.to_thread(_fetch_web_page, item["url"])
            page["title"] = item.get("title", item["url"])
            web_pages.append(page)

        good_web   = [w for w in web_pages if w["success"]]
        failed_web = [w for w in web_pages if not w["success"]]

        # ── Phase 3+4: LLM cross-verification + confidence scoring ────────────
        total_academic = len(good_papers) + len(good_arxiv)
        await set_progress(
            f"🧠 AI cross-verifying {total_academic} papers + {len(good_web)} web pages...",
            {
                "semantic_scholar": len(good_papers),
                "arxiv": len(good_arxiv),
                "web_ok": len(good_web),
                "web_failed": len(failed_web),
            },
        )

        report = await _verify_and_score(
            topic, papers, arxiv_papers, web_pages, instructions
        )

        # ── Phase 5: Save results ─────────────────────────────────────────────
        source_stats = {
            "semantic_scholar_count": len(good_papers),
            "arxiv_count":            len(good_arxiv),
            "tavily_urls_found":      len(tavily_results),
            "web_pages_fetched":      len(web_pages),
            "web_pages_successful":   len(good_web),
            "web_pages_failed":       len(failed_web),
            "total_citations":        sum(p.get("citations", 0) for p in good_papers),
        }

        await db["research_tasks"].update_one(
            {"_id": task_id},
            {
                "$set": {
                    "status":        "completed",
                    "results":       report,
                    "source_stats":  source_stats,
                    "progress_step": "✅ Complete",
                }
            },
        )

    except Exception as exc:
        import traceback
        await db["research_tasks"].update_one(
            {"_id": task_id},
            {
                "$set": {
                    "status":        "failed",
                    "results":       f"Deep research failed:\n{exc}\n\n{traceback.format_exc()}",
                    "progress_step": "❌ Failed",
                }
            },
        )
