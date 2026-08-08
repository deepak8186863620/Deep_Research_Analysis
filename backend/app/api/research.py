import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.research import ResearchRequest, ResearchResponse
from app.core.database import get_database
from app.services.research_agent import run_research_task
from app.services.deep_research_agent import run_deep_research_task

router = APIRouter(prefix="/api/research", tags=["Research"])


@router.get("/", response_model=list)
async def list_research_tasks(limit: int = 30):
    """List the most recent research tasks (newest first) for sidebar history."""
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    cursor = db["research_tasks"].find(
        {},
        {"_id": 1, "topic": 1, "status": 1, "created_at": 1, "mode": 1}
    ).sort("created_at", -1).limit(limit)

    tasks = []
    async for doc in cursor:
        tasks.append({
            "id":         doc["_id"],
            "topic":      doc["topic"],
            "status":     doc["status"],
            "mode":       doc.get("mode", "quick"),
            "created_at": doc.get("created_at"),
        })
    return tasks


@router.post("/", response_model=ResearchResponse)
async def create_research_task(request: ResearchRequest, background_tasks: BackgroundTasks):
    """
    Create a new research task.
    mode='quick' → LangGraph + FAISS agent (fast, ~1 min)
    mode='deep'  → Multi-source + SHA-256 verification + confidence scoring (~3-5 min)
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    task_id = str(uuid.uuid4())
    now     = datetime.now(timezone.utc)

    research_doc = {
        "_id":          task_id,
        "topic":        request.topic,
        "instructions": request.instructions,
        "mode":         request.mode,
        "status":       "pending",
        "progress_step": "Queued...",
        "progress_details": {},
        "created_at":   now,
        "results":      None,
        "source_stats": None,
    }

    await db["research_tasks"].insert_one(research_doc)

    # Route to the correct agent based on mode
    if request.mode == "deep":
        background_tasks.add_task(
            run_deep_research_task, task_id, request.topic, request.instructions
        )
    else:
        background_tasks.add_task(
            run_research_task, task_id, request.topic, request.instructions
        )

    return ResearchResponse(
        id=task_id,
        topic=request.topic,
        status="pending",
        mode=request.mode,
        created_at=now,
    )


@router.get("/{task_id}")
async def get_research_status(task_id: str):
    """Get the current status, progress, and results of a research task."""
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    doc = await db["research_tasks"].find_one({"_id": task_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "id":               doc["_id"],
        "topic":            doc["topic"],
        "instructions":     doc.get("instructions"),
        "mode":             doc.get("mode", "quick"),
        "status":           doc["status"],
        "progress_step":    doc.get("progress_step", ""),
        "progress_details": doc.get("progress_details", {}),
        "results":          doc.get("results"),
        "source_stats":     doc.get("source_stats"),
        "created_at":       doc["created_at"],
    }


@router.delete("/{task_id}", status_code=204)
async def delete_research_task(task_id: str):
    """Delete a research task from the database."""
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    result = await db["research_tasks"].delete_one({"_id": task_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
