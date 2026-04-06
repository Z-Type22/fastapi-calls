from pydantic import BaseModel
from src.users.schemas import UserRead
from typing import List
from datetime import datetime


class CallRead(BaseModel):
    id: int
    title: str
    caller: UserRead
    callees: List[UserRead]
    created_at: datetime
    uuid: str

    model_config = {
        "from_attributes": True
    }


class CalleeSchema(BaseModel):
    call_id: int
    callee_id: int


class CallCreate(BaseModel):
    title: str


class Message(BaseModel):
    detail: str
