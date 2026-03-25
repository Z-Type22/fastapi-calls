from src.database import Base
from enum import Enum
from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    Boolean, 
    Enum as ModelEnum
)


class User(Base):

    class Gender(str, Enum):
        MAN = "man"
        WOMAN = "woman"
        OTHERS = "others"

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    gender = Column(ModelEnum(Gender), nullable=False, default=Gender.OTHERS)
    avatar = Column(String, nullable=True)
