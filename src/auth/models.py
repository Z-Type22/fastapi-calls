from src.database import Base
from sqlalchemy import Column, DateTime, String


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    jti = Column(String, primary_key=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
