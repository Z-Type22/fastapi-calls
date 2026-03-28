from pydantic import BaseModel
from src.users.schemas import UserRead
from typing import List
from datetime import datetime


class CallRead(BaseModel):
    id: int
    caller_id: int
    callees: List[UserRead]
    created_at: datetime
    is_private: bool

    model_config = {
        "from_attributes": True
    }


class CalleeSchema(BaseModel):
    call_id: int
    callee_id: int


class CallCreate(BaseModel):
    is_private: bool
