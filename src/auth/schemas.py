from pydantic import BaseModel, EmailStr, Field, field_validator
from src.users.models import User


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password1: str = Field(..., min_length=8)
    password2: str = Field(..., min_length=8)
    gender: User.Gender | None = None

    @field_validator("password2")
    def passwords_match(cls, value, info):
        if "password1" in info.data and value != info.data["password1"]:
            raise ValueError("Passwords do not match")
        return value
    
class UserLogin(BaseModel):
    username: str
    password: str


class TokensSchema(BaseModel):
    token_type: str = "Bearer"
    refresh_token: str
    access_token: str
