from pydantic import BaseModel
from src.calls.models import Call
from datetime import datetime


class CallRead(BaseModel):
    id: int
    caller_id: int
    callee_id: int
    status: Call.Status
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class CallCreate(BaseModel):
    callee_id: int


class Message(BaseModel):
    detail: str
