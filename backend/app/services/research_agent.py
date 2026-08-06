from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from app.core.config import settings
from app.core.database import get_database

# 1. Define the State
# The "State" is what gets passed around between nodes in our graph.
# We are just passing a list of messages (the conversation history + tool outputs).
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# 2. Define Tools
# We give the AI the ability to search the web using Tavily.
tavily_tool = TavilySearchResults(max_results=3, tavily_api_key=settings.TAVILY_API_KEY)
tools = [tavily_tool]

# 3. Initialize the AI Model
# We use Google's Gemini-1.5-pro and "bind" the tools to it so it knows it can use them.
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro", 
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0.2 # low temperature so it gives factual answers rather than creative ones
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

# Logic: Start -> Agent -> If tool called -> Tools -> Agent -> If finished -> End
workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent",
    tools_condition,
    {"tools": "tools", END: END}
)
workflow.add_edge("tools", "agent")

# Compile the graph into an executable agent
research_graph = workflow.compile()


async def run_research_task(task_id: str, topic: str, instructions: str = None):
    """
    This function runs the actual research graph. It will update the MongoDB
    status so the frontend knows if it's processing, completed, or failed.
    """
    db = get_database()
    
    # 1. Update Database Status to "processing"
    await db["research_tasks"].update_one(
        {"_id": task_id},
        {"$set": {"status": "processing"}}
    )
    
    try:
        # 2. Build the initial prompt for the AI
        prompt = f"Conduct deep research on the following topic: {topic}\n"
        prompt += "Provide a comprehensive, well-structured summary of your findings."
        if instructions:
            prompt += f"\nSpecific Instructions to follow: {instructions}"
        
        initial_state = {"messages": [HumanMessage(content=prompt)]}
        
        # 3. Run the LangGraph agent
        final_state = await research_graph.ainvoke(initial_state)
        
        # Extract the final textual answer from the last message in the state
        final_answer = final_state["messages"][-1].content
        
        # 4. Save the results and mark as "completed" in MongoDB
        await db["research_tasks"].update_one(
            {"_id": task_id},
            {"$set": {"status": "completed", "results": final_answer}}
        )
        
    except Exception as e:
        # 5. If anything crashes, mark it as "failed" so the user isn't stuck waiting forever
        await db["research_tasks"].update_one(
            {"_id": task_id},
            {"$set": {"status": "failed", "results": str(e)}}
        )
