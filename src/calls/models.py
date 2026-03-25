from src.database import Base
from src.users.models import User
from enum import Enum
from sqlalchemy import (
    Column, 
    Integer, 
    String,  
    Enum as ModelEnum,
    ForeignKey,
    DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid


class Call(Base):

    class Status(str, Enum):
        CREATED = "created"
        RINGING = "ringing"
        ACCEPTED = "accepted"
        REJECTED = "rejected"
        ENDED = "ended"

    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)

    uuid = Column(
        String,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
        index=True,
    )
    caller_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    callee_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    status = Column(ModelEnum(Status), nullable=False, default=Status.CREATED)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    caller = relationship(
        User,
        foreign_keys=[caller_id],
        backref="outgoing_calls"
    )
    callee = relationship(
        User,
        foreign_keys=[callee_id],
        backref="incoming_calls"
    )

    def can_join(self, user: User) -> bool:
        return user.id in (self.caller_id, self.callee_id)
