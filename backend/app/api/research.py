import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.research import ResearchRequest, ResearchResponse
from app.core.database import get_database
from app.services.research_agent import run_research_task

# We create an APIRouter to group all research-related endpoints together
router = APIRouter(prefix="/api/research", tags=["Research"])

@router.post("/", response_model=ResearchResponse)
async def create_research_task(request: ResearchRequest, background_tasks: BackgroundTasks):
    """
    Endpoint to receive a research topic, save it to the database as 'pending',
    and return the task ID to the user.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    # Generate a unique ID for this research task
    task_id = str(uuid.uuid4())
    
    # Prepare the document to store in MongoDB
    research_doc = {
        "_id": task_id,
        "topic": request.topic,
        "instructions": request.instructions,
        "status": "pending",  # Later, our AI will change this to 'processing' and then 'completed'
        "created_at": datetime.now(timezone.utc),
        "results": None
    }
    
    # Insert the document into a MongoDB collection named 'research_tasks'
    await db["research_tasks"].insert_one(research_doc)
    
    # Launch the AI research task in the background!
    # This allows the API to return the response immediately without waiting for the AI to finish.
    background_tasks.add_task(run_research_task, task_id, request.topic, request.instructions)
    
    # Return the response matching our Pydantic ResearchResponse model
    return ResearchResponse(
        id=task_id,
        topic=request.topic,
        status="pending",
        created_at=research_doc["created_at"]
    )

@router.get("/{task_id}")
async def get_research_status(task_id: str):
    """
    Endpoint to check the status and results of a research task.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    doc = await db["research_tasks"].find_one({"_id": task_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return {
        "id": doc["_id"],
        "topic": doc["topic"],
        "status": doc["status"],
        "results": doc.get("results"),
        "created_at": doc["created_at"]
    }
