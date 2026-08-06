import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.models.research import ResearchRequest, ResearchResponse
from app.core.database import get_database

# We create an APIRouter to group all research-related endpoints together
router = APIRouter(prefix="/api/research", tags=["Research"])

@router.post("/", response_model=ResearchResponse)
async def create_research_task(request: ResearchRequest):
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
    
    # Return the response matching our Pydantic ResearchResponse model
    return ResearchResponse(
        id=task_id,
        topic=request.topic,
        status="pending",
        created_at=research_doc["created_at"]
    )
