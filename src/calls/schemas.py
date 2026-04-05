from pydantic import BaseModel
from src.users.schemas import UserRead
from typing import List
from datetime import datetime


class CallRead(BaseModel):
    id: int
    caller: UserRead
    callees: List[UserRead]
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class CalleeSchema(BaseModel):
    call_id: int
    callee_id: int


class Message(BaseModel):
    detail: str
