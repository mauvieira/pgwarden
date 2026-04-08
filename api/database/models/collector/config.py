from sqlalchemy import (
    Column, BigInteger, Text, 
    Integer, Boolean, DateTime, func
)
from database.models.base_model import Base


class Config(Base):
    __tablename__ = "config"
    __table_args__ = {"schema": "collector"}

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    name        = Column(Text, nullable=False, unique=True)
    interval    = Column(Integer, nullable=False)
    is_paused   = Column(Boolean, nullable=False, default=False)
    status      = Column(Text, nullable=False, default='idle')
    next_run_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    last_error  = Column(Text, nullable=True)
    run_count   = Column(BigInteger, nullable=False, default=0)
    error_count = Column(BigInteger, nullable=False, default=0)
    updated_at  = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
