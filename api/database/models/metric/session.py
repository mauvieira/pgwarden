from sqlalchemy import (
    Column, BigInteger, Integer, 
    DateTime, Text, ForeignKey
)
from sqlalchemy.dialects.postgresql import INET
from database.models.base_model import Base


class SessionMetric(Base):
    __tablename__ = "session"
    __table_args__ = {"schema": "metric"}

    collected_at     = Column(DateTime(timezone=True), primary_key=True)
    database_id      = Column(BigInteger, ForeignKey("metadata.database.id", ondelete="CASCADE"), primary_key=True)
    pid              = Column(Integer, primary_key=True)
    backend_start    = Column(DateTime(timezone=True), primary_key=True)
    user_name        = Column(Text, nullable=True)
    application_name = Column(Text, nullable=True)
    client_addr      = Column(INET, nullable=True)
    state            = Column(Text, nullable=True)
    wait_event_type  = Column(Text, nullable=True)
    wait_event       = Column(Text, nullable=True)
    query_start      = Column(DateTime(timezone=True), nullable=True)
    state_change     = Column(DateTime(timezone=True), nullable=True)
    query_preview    = Column(Text, nullable=True)
