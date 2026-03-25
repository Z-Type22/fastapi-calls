from pydantic import BaseModel, EmailStr
from src.users.models import User


class UserRead(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    username: str
    avatar: str | None = None
    gender: User.Gender

    model_config = {
        "from_attributes": True
    }
