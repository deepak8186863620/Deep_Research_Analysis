"""
prompts/research_prompts.py

PURPOSE: Central store for all prompt templates used by the research agent.

WHY A SEPARATE FILE?
  Prompts are not code — they are instructions written in natural language
  that tell the LLM how to behave. Keeping them here means:
  1. You can improve/tweak prompts without touching agent logic.
  2. You can version-control prompt changes separately from code changes.
  3. Other agents or endpoints can reuse the same prompt templates.
"""

from typing import Optional


def build_research_prompt(topic: str, instructions: Optional[str] = None) -> str:
    """
    PURPOSE: Builds the full research prompt sent to the LangGraph agent.

    This prompt tells the AI exactly HOW to research:
      - Which tools to use and in which order
      - How to compare academic vs web sources
      - What format the final answer must follow

    The structured 4-step format is critical — without it, the LLM might
    skip Semantic Scholar entirely and just use Tavily, or vice versa.
    The comparison step (Step 3) is what separates this from a simple search.

    Args:
        topic:        The research topic submitted by the user.
        instructions: Optional extra instructions from the user
                      (e.g. "Focus only on 2023-2024 papers").

    Returns:
        A fully formatted prompt string ready to be wrapped in a HumanMessage.
    """
    prompt = (
        f"Conduct deep research on the following topic: {topic}\n\n"

        "Follow these steps strictly in order:\n\n"

        # ── STEP 1: Academic Research ──────────────────────────────────────
        # We always start with academia because:
        # - Peer-reviewed = fact-checked by other experts
        # - Citation count = how many researchers trusted this paper
        # - Provides foundational, long-term knowledge (not just recent trends)
        "STEP 1 — ACADEMIC RESEARCH (use search_semantic_scholar):\n"
        "  Search for the top peer-reviewed papers on this topic.\n"
        "  Sort by citation count — most cited = most trusted by the scientific community.\n"
        "  Then use search_indexed_papers to extract specific facts, numbers, and findings.\n\n"

        # ── STEP 2: Web/Current Research ──────────────────────────────────
        # Web search fills the gap that academia can't:
        # - Academic papers take 1-3 years to publish (always slightly outdated)
        # - Web has industry reports, product releases, real-world benchmarks
        # - Provides practical, applied context for the academic findings
        "STEP 2 — CURRENT WEB RESEARCH (use Tavily search):\n"
        "  Search for the latest news, industry reports, blog posts,\n"
        "  and real-world applications of this topic.\n"
        "  Focus on developments from the last 1-2 years that academia may not cover yet.\n\n"

        # ── STEP 3: Cross-Source Comparison ───────────────────────────────
        # This is the unique value-add of this system.
        # Simply listing both sources isn't enough — the AI must actively compare
        # and reason about where they agree, disagree, or diverge.
        "STEP 3 — COMPARISON & SYNTHESIS:\n"
        "  Compare what academic papers say vs what current web sources say.\n"
        "  Identify:\n"
        "    a) AGREEMENTS  — Points both sources confirm. These are high-confidence facts.\n"
        "    b) CONFLICTS   — Points where they disagree. Flag these clearly for the user.\n"
        "    c) GAPS        — Topics the web discusses but academia hasn't studied yet.\n\n"

        # ── STEP 4: Final Structured Report ───────────────────────────────
        # A structured format makes the output scannable and professional.
        # Users can jump directly to the section they care about.
        "STEP 4 — FINAL REPORT (use this exact structure):\n"
        "  ## Summary\n"
        "  (2-3 sentence overview of the entire topic)\n\n"
        "  ## Academic Findings\n"
        "  (Key findings from papers. For each, include: Title, Year, Citation Count)\n\n"
        "  ## Current Developments\n"
        "  (Recent news, industry trends, real-world applications from web sources)\n\n"
        "  ## Key Agreements\n"
        "  (What both academic papers AND web sources agree on — highest confidence)\n\n"
        "  ## Conflicts or Contradictions\n"
        "  (Where academic papers and web sources disagree — flag these for the user)\n\n"
        "  ## Conclusion\n"
        "  (Your final synthesized answer to the research question)\n"
    )

    # Append any user-specific instructions at the end
    # These override or narrow down the general research focus
    if instructions:
        prompt += (
            f"\n---\n"
            f"Additional Instructions from the user (follow these carefully):\n"
            f"{instructions}\n"
        )

    return prompt


def build_followup_prompt(original_topic: str, followup_question: str) -> str:
    """
    PURPOSE: Builds a prompt for follow-up questions on an already-researched topic.

    WHY NEEDED: After receiving a research report, a user might ask a deeper
    follow-up question like "Can you explain the attention mechanism in more detail?"
    This prompt is optimized for that scenario — it assumes papers are already
    indexed in FAISS and skips Step 1 (no need to re-fetch papers).

    Args:
        original_topic:   The original topic that was researched.
        followup_question: The user's new, specific question.

    Returns:
        A prompt string for follow-up querying.
    """
    return (
        f"The user previously researched: '{original_topic}'.\n"
        f"They now have a follow-up question: '{followup_question}'\n\n"
        "Use search_indexed_papers to find the answer from the already-indexed papers.\n"
        "If the papers don't contain enough information, use search_semantic_scholar "
        "or Tavily to find more.\n"
        "Provide a concise, direct answer focused specifically on the follow-up question."
    )
