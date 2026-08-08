from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class ResearchRequest(BaseModel):
    """Request payload sent by the frontend to create a research task."""
    topic: str = Field(
        ...,
        description="The main topic to research",
        examples=["Quantum computing advancements in 2024"],
    )
    instructions: Optional[str] = Field(
        None,
        description="Specific instructions for the AI",
        examples=["Focus only on hardware, ignore software"],
    )
    mode: Literal["quick", "deep"] = Field(
        "quick",
        description=(
            "Research mode: "
            "'quick' = LangGraph agent with FAISS (fast, ~1 min); "
            "'deep'  = Full multi-source verification with confidence scoring (~3-5 min)"
        ),
    )


class ResearchResponse(BaseModel):
    """Immediate response returned after creating a task (before research completes)."""
    id: str
    topic: str
    status: str
    mode: str
    created_at: datetime
