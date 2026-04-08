from sqlalchemy import (
    Column, BigInteger, Text, 
    DateTime, func
)
from sqlalchemy.dialects.postgresql import JSONB
from database.models.base_model import Base


class Command(Base):
    __tablename__ = "command"
    __table_args__ = {"schema": "collector"}

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    collector   = Column(Text, nullable=False)
    command     = Column(Text, nullable=False)
    payload     = Column(JSONB, nullable=True)
    created_at  = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    executed_at = Column(DateTime(timezone=True), nullable=True)
    error       = Column(Text, nullable=True)
