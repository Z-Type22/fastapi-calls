from src.database import Base
from src.users.models import User
from sqlalchemy import (
    Column, 
    Integer, 
    String,
    ForeignKey,
    DateTime,
    Table,
    Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid


class Call(Base):
    __tablename__ = "calls"

    call_callees = Table(
        "call_callees",
        Base.metadata,
        Column(
            "call_id",
            Integer,
            ForeignKey("calls.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        Column(
            "user_id",
            Integer,
            ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    caller = relationship(
        User,
        foreign_keys=[caller_id],
        backref="outgoing_calls"
    )
    callees = relationship(
        User,
        secondary=call_callees,
        backref="incoming_calls",
        lazy="noload",
    )
    is_private = Column(Boolean, default=False, nullable=False)

    def can_join(self, user: User) -> bool:
        return (
            user.id == self.caller_id
            or any(callee.id == user.id for callee in self.callees)
        )
