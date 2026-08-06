from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ResearchRequest(BaseModel):
    """
    This model defines exactly what the frontend must send us when requesting a new research topic.
    """
    topic: str = Field(..., description="The main topic to research", examples=["Quantum computing advancements in 2024"])
    instructions: Optional[str] = Field(None, description="Any specific instructions for the AI", examples=["Focus only on hardware, ignore software"])

class ResearchResponse(BaseModel):
    """
    This model defines what we send back to the frontend immediately after they submit a request.
    """
    id: str
    topic: str
    status: str
    created_at: datetime
