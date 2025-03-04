from pydantic import BaseModel, Field
import uuid

class DebateParams(BaseModel):
    """Parameters for a debate."""
    debate_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str
    human_side: str

    class Config:
        schema_extra = {
            "example": {
                "debate_id": "550e8400-e29b-41d4-a716-446655440000",
                "topic": "Is artificial intelligence beneficial for humanity?",
                "human_side": "con"
            }
        }
