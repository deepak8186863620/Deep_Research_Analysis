from typing import Annotated, Sequence, TypedDict, Optional
from bson import ObjectId
from bson.errors import InvalidId

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch  # replaces deprecated TavilySearchResults
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from app.core.config import settings
from app.core.database import get_database


# 1. Define the State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


# 2. Define Tools
tavily_tool = TavilySearch(max_results=3, tavily_api_key=settings.TAVILY_API_KEY)
tools = [tavily_tool]

# 3. Initialize the AI Model
# NOTE: gemini-1.5-pro is retired. Use a currently-supported model and keep
# it in settings so you can swap it without a code change when Google
# deprecates the next one.
llm = ChatGoogleGenerativeAI(
    model=getattr(settings, "GEMINI_MODEL", "gemini-2.5-pro"),
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0.2,
)
llm_with_tools = llm.bind_tools(tools)


# 4. Define Nodes
def agent_node(state: AgentState):
    """The AI node that decides what to do next."""
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


tool_node = ToolNode(tools)

# 5. Build the LangGraph Workflow
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


def _to_mongo_id(task_id: str):
    """
    Convert a task_id string to the type actually used for _id in Mongo.
    If your collection was inserted with Mongo's default ObjectId, task_id
    (a plain string) will NEVER match a bare string query — this fixes that.
    If you instead store _id as a plain string yourself, this just falls
    back to the original string safely.
    """
    try:
        return ObjectId(task_id)
    except (InvalidId, TypeError):
        return task_id


def _extract_text(message: BaseMessage) -> str:
    """Safely pull text out of the final AI message, whatever shape it's in."""
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # Some providers return content as a list of parts (text/tool blocks)
        parts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"]
        return "\n".join(parts) if parts else str(content)
    return str(content)


async def run_research_task(task_id: str, topic: str, instructions: Optional[str] = None):
    """
    Runs the research graph and updates MongoDB with status: processing,
    completed, or failed.
    """
    db = get_database()
    mongo_id = _to_mongo_id(task_id)

    await db["research_tasks"].update_one(
        {"_id": mongo_id},
        {"$set": {"status": "processing"}},
    )

    try:
        prompt = f"Conduct deep research on the following topic: {topic}\n"
        prompt += "Provide a comprehensive, well-structured summary of your findings."
        if instructions:
            prompt += f"\nSpecific Instructions to follow: {instructions}"

        initial_state = {"messages": [HumanMessage(content=prompt)]}

        # recursion_limit guards against an agent<->tools loop that never
        # converges (e.g. the model keeps calling search without answering)
        final_state = await research_graph.ainvoke(
            initial_state,
            config={"recursion_limit": 15},
        )

        final_answer = _extract_text(final_state["messages"][-1])

        await db["research_tasks"].update_one(
            {"_id": mongo_id},
            {"$set": {"status": "completed", "results": final_answer}},
        )

    except Exception as e:
        await db["research_tasks"].update_one(
            {"_id": mongo_id},
            {"$set": {"status": "failed", "results": str(e)}},
        )