from sqlalchemy import (
    Column, BigInteger, Text, 
    Boolean, Integer, DateTime, func, ForeignKey
)
from database.models.base_model import Base


class ColumnHistory(Base):
    __tablename__ = "column_history"
    __table_args__ = {"schema": "metadata"}

    id               = Column(BigInteger, primary_key=True, autoincrement=True)
    column_id        = Column(BigInteger, ForeignKey("metadata.column.id"), nullable=False)
    table_id         = Column(BigInteger, ForeignKey("metadata.table.id"), nullable=False)
    name             = Column(Text, nullable=False)
    description      = Column(Text, nullable=True)
    data_type        = Column(Text, nullable=False)
    is_nullable      = Column(Boolean, nullable=False)
    default_value    = Column(Text, nullable=True)
    is_unique        = Column(Boolean, nullable=False)
    ordinal_position = Column(Integer, nullable=False)
    fk_table_id      = Column(BigInteger, nullable=True)
    fk_column_id     = Column(BigInteger, nullable=True)
    changed_at       = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    changed_by       = Column(BigInteger, nullable=True)
