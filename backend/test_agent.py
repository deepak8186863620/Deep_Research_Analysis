import asyncio
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from app.services.deep_research_agent import (
    _fetch_semantic_scholar,
    _fetch_arxiv,
    _fetch_tavily_multi,
    _fetch_web_page,
    _verify_and_score
)

async def main():
    topic = "transformer attention neural network"
    print(f"Testing Research on topic: {topic}\n")

    print("1. Fetching Semantic Scholar...")
    papers = _fetch_semantic_scholar(topic, limit=2)
    print(f"Found {len(papers)} papers from Semantic Scholar.")

    print("2. Fetching arXiv...")
    arxiv_papers = _fetch_arxiv(topic, max_results=2)
    print(f"Found {len(arxiv_papers)} papers from arXiv.")

    print("3. Fetching Tavily...")
    tavily_results = _fetch_tavily_multi(topic)
    print(f"Found {len(tavily_results)} URLs from Tavily.")

    urls_to_fetch = tavily_results[:2]
    web_pages = []
    print("4. Fetching Web Pages...")
    for item in urls_to_fetch:
        page = _fetch_web_page(item["url"])
        page["title"] = item.get("title", item["url"])
        web_pages.append(page)
    print(f"Fetched {len(web_pages)} web pages.")

    print("5. Verifying and Scoring (Gemini)...")
    report = await _verify_and_score(topic, papers, arxiv_papers, web_pages, "Give a very short summary.")
    print("\n=== FINAL REPORT ===\n")
    print(report)

if __name__ == "__main__":
    asyncio.run(main())
