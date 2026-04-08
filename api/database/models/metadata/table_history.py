from sqlalchemy import (
    Column, BigInteger, Text, 
    DateTime, func, ForeignKey
)
from database.models.base_model import Base


class TableHistory(Base):
    __tablename__ = "table_history"
    __table_args__ = {"schema": "metadata"}

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    table_id    = Column(BigInteger, ForeignKey("metadata.table.id"), nullable=False)
    table_oid   = Column(BigInteger, nullable=False)
    schema_name = Column(Text, nullable=False)
    name        = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    changed_at  = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    changed_by  = Column(BigInteger, nullable=True)
