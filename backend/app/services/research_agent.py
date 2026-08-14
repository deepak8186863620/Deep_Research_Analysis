from typing import Annotated, Sequence, TypedDict, Optional

import requests
from bson import ObjectId
from bson.errors import InvalidId

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from app.core.config import settings
from app.core.database import get_database
from app.utils.text_utils import extract_text_from_message, clean_whitespace
from app.prompts.research_prompts import build_research_prompt


# ─────────────────────────────────────────────────────────────────────────────
# 1. AGENT STATE
# PURPOSE: The "memory" of the agent. Every message (user prompt, tool call,
#          tool result, AI reply) gets appended here automatically by
#          add_messages. The agent always sees the full conversation history.
# ─────────────────────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


# ─────────────────────────────────────────────────────────────────────────────
# 2. AI MODEL
# PURPOSE: The brain of the agent. It reads the full conversation history
#          and decides: "Should I call a tool?" or "Am I ready to answer?"
#          Created once at module level and reused across all tasks.
# ─────────────────────────────────────────────────────────────────────────────
llm = ChatGoogleGenerativeAI(
    model=getattr(settings, "GEMINI_MODEL", "gemini-2.5-pro"),
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0.2,  # Low = more factual, less creative
)


# ─────────────────────────────────────────────────────────────────────────────
# 3. EMBEDDINGS MODEL
# PURPOSE: Converts text into vectors (numbers that represent meaning).
#          "neural network" and "deep learning" get similar vectors even
#          though they are different words. This is how FAISS searches
#          by meaning instead of exact keyword matching.
#          all-MiniLM-L6-v2 is a small, fast model that runs fully offline.
# ─────────────────────────────────────────────────────────────────────────────
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


# ─────────────────────────────────────────────────────────────────────────────
# 4. TEXT SPLITTER
# PURPOSE: A research paper is 5,000–15,000 words — too long for any LLM
#          to read all at once. This cuts papers into 1000-character chunks.
#          chunk_overlap=150 means the last 150 characters of chunk 1 are
#          repeated at the start of chunk 2, so no sentence is ever cut
#          in half and context is preserved across boundaries.
# ─────────────────────────────────────────────────────────────────────────────
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    length_function=len,
)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _to_mongo_id(task_id: str):
    """
    Our API stores _id as a plain UUID string.
    This helper safely handles both UUID strings and ObjectIds.
    """
    try:
        return ObjectId(task_id)
    except (InvalidId, TypeError):
        return task_id


# _extract_text is now imported from app.utils.text_utils as extract_text_from_message
# clean_whitespace is imported too — used to clean paper abstracts before chunking


# ─────────────────────────────────────────────────────────────────────────────
# 5. TOOL FACTORY
# PURPOSE: Builds 3 tools that share a single FAISS index for one task.
#
#          WHY A FACTORY? Each research task needs its own private FAISS index.
#          If User A researches "climate change" and User B researches "BERT",
#          their papers must never mix. The factory creates fresh tools
#          (with a fresh empty FAISS index) every time run_research_task runs.
#          When the task finishes, Python garbage-collects the index automatically.
# ─────────────────────────────────────────────────────────────────────────────
def _build_research_tools(faiss_index: dict):
    """
    faiss_index = {"store": None}   ← starts empty
    Tool B fills it. Tool C reads from it. Both share the same dict object.
    """

    # ── TOOL A: Tavily Web Search ────────────────────────────────────────────
    # PURPOSE: General web search for current events, news, product docs,
    #          and anything that isn't in academic paper databases.
    #          Example use: "latest GPU benchmarks 2024", "OpenAI news"
    # ────────────────────────────────────────────────────────────────────────
    tavily_tool = TavilySearch(max_results=3, tavily_api_key=settings.TAVILY_API_KEY)

    # ── TOOL B: Semantic Scholar Search ──────────────────────────────────────
    # PURPOSE: Fetches top peer-reviewed academic papers for a query.
    #   Step 1 → Calls Semantic Scholar API (free, no key needed)
    #   Step 2 → Sorts results by citation count (most cited = most trusted)
    #   Step 3 → Chunks each abstract with text_splitter
    #   Step 4 → Stores chunks in the shared FAISS index
    #   Step 5 → Returns paper titles + abstracts for the AI to read
    # ─────────────────────────────────────────────────────────────────────────
    @tool
    def search_semantic_scholar(query: str) -> str:
        """
        Search Semantic Scholar for peer-reviewed academic papers on a topic.
        Returns paper titles, years, citation counts, and full abstracts.
        Also indexes the papers into FAISS so search_indexed_papers can
        find specific details later. Use this for any scientific or academic topic.
        """
        try:
            response = requests.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={
                    "query": query,
                    "fields": "title,authors,year,abstract,citationCount",
                    "limit": 10,
                },
                timeout=10,
            )
            response.raise_for_status()
            papers = response.json().get("data", [])

            if not papers:
                return "No academic papers found for this query on Semantic Scholar."

            # Most cited = most peer-validated = most trustworthy
            papers.sort(key=lambda p: p.get("citationCount") or 0, reverse=True)

            output_lines = []
            docs_to_index = []

            for p in papers:
                # clean_whitespace removes extra newlines/spaces from API responses
                # PURPOSE: Better quality text = better quality embeddings in FAISS
                raw_abstract = p.get("abstract") or "No abstract available."
                abstract  = clean_whitespace(raw_abstract)
                title     = p.get("title", "Unknown Title")
                year      = p.get("year", "N/A")
                citations = p.get("citationCount", 0)

                # This text goes into the agent's context window (what the AI reads)
                summary = (
                    f"Title: {title}\n"
                    f"Year: {year} | Citations: {citations}\n"
                    f"Abstract: {abstract}"
                )
                output_lines.append(summary)

                # These chunks go into FAISS (for deep semantic search later)
                # Each chunk carries metadata so we know which paper it came from
                chunks = text_splitter.create_documents(
                    texts=[abstract],
                    metadatas=[{"title": title, "year": year, "citations": citations}]
                )
                docs_to_index.extend(chunks)

            # First call → create a fresh FAISS index from the chunks
            # Later calls → add new paper chunks to the existing index
            if faiss_index["store"] is None:
                faiss_index["store"] = FAISS.from_documents(docs_to_index, embeddings)
            else:
                faiss_index["store"].add_documents(docs_to_index)

            return "\n\n---\n\n".join(output_lines)

        except Exception as e:
            return f"Error querying Semantic Scholar: {str(e)}"

    # ── TOOL C: FAISS Deep Search ─────────────────────────────────────────────
    # PURPOSE: Lets the agent dig into specific details from papers already
    #          fetched by Tool B without calling the API again.
    #          Example: After fetching 10 papers on "transformers", the agent
    #          can ask "what did these papers say about attention heads?" and
    #          FAISS instantly returns the 4 most relevant chunks by meaning.
    # ─────────────────────────────────────────────────────────────────────────
    @tool
    def search_indexed_papers(query: str) -> str:
        """
        Search by meaning through the academic papers already fetched and
        indexed in FAISS. Use this to find specific facts, quotes, or details
        from papers previously loaded via search_semantic_scholar.
        Always call search_semantic_scholar at least once before using this.
        """
        if faiss_index["store"] is None:
            return "No papers indexed yet. Call search_semantic_scholar first."

        # k=4 → return the 4 most semantically similar chunks
        results = faiss_index["store"].similarity_search(query, k=4)

        if not results:
            return "No relevant content found in the indexed papers."

        output = []
        for doc in results:
            meta = doc.metadata
            output.append(
                f"[Source: '{meta.get('title', 'Unknown')}' "
                f"({meta.get('year', 'N/A')}) — {meta.get('citations', 0)} citations]\n"
                f"{doc.page_content}"
            )

        return "\n\n---\n\n".join(output)

    return [tavily_tool, search_semantic_scholar, search_indexed_papers]


# ─────────────────────────────────────────────────────────────────────────────
# 6. MAIN RESEARCH FUNCTION
# PURPOSE: The entry point called by FastAPI's background task system.
#   1. Marks the task as "processing" in MongoDB
#   2. Builds fresh tools + a private FAISS index for this task
#   3. Builds and runs the LangGraph agent
#   4. Saves the final answer (or error message) back to MongoDB
# ─────────────────────────────────────────────────────────────────────────────
async def run_research_task(task_id: str, topic: str, instructions: Optional[str] = None):
    db = get_database()
    mongo_id = _to_mongo_id(task_id)

    await db["research_tasks"].update_one(
        {"_id": mongo_id},
        {"$set": {"status": "processing"}},
    )

    try:
        # Each task starts with an empty FAISS index (isolated per task)
        faiss_index = {"store": None}

        # Create the 3 tools for this specific task
        tools = _build_research_tools(faiss_index)

        # Tell the LLM which tools it can use
        llm_with_tools = llm.bind_tools(tools)

        # Agent node: AI reads all messages and decides the next action
        def agent_node(state: AgentState):
            response = llm_with_tools.invoke(state["messages"])
            return {"messages": [response]}

        # Tool node: Executes whichever tool the AI decided to call
        tool_node = ToolNode(tools)

        # Build the LangGraph workflow for this task:
        # START → agent → (tool needed?) → tools → agent → ... → END
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", tool_node)
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges(
            "agent",
            tools_condition,
            {"tools": "tools", END: END},
        )
        workflow.add_edge("tools", "agent")
        research_graph = workflow.compile()

        # PURPOSE: build_research_prompt is imported from app/prompts/research_prompts.py
        # Keeping prompts in a separate file means we can improve the instructions
        # without touching any agent logic here.
        prompt = build_research_prompt(topic, instructions)

        # recursion_limit=25: agent can do at most 25 tool-call rounds
        # (prevents infinite loops if the model keeps searching without answering)
        final_state = await research_graph.ainvoke(
            {"messages": [HumanMessage(content=prompt)]},
            config={"recursion_limit": 50},
        )

        # extract_text_from_message is imported from app/utils/text_utils.py
        # It handles both plain string and list-of-blocks content formats
        final_answer = extract_text_from_message(final_state["messages"][-1].content)

        await db["research_tasks"].update_one(
            {"_id": mongo_id},
            {"$set": {"status": "completed", "results": final_answer}},
        )

    except Exception as e:
        await db["research_tasks"].update_one(
            {"_id": mongo_id},
            {"$set": {"status": "failed", "results": str(e)}},
        )