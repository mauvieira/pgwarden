from sqlalchemy import (
    Column, Integer, DateTime,
    ForeignKey, func, Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from database.models.base_model import Base


class Refresh(Base):
    __tablename__ = "refresh"
    __table_args__ = {"schema": "base"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("base.user.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(UUID(as_uuid=True), nullable=False, unique=True, default=uuid.uuid4)
    used = Column(Boolean, nullable=False, default=False)
    inserted_at = Column(DateTime, nullable=False, default=func.now())

    user = relationship("User", back_populates="refresh_tokens")