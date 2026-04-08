from sqlalchemy import (
    Column, BigInteger, Text, 
    DateTime, func, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from database.models.base_model import Base


class Table(Base):
    __tablename__ = "table"
    __table_args__ = {"schema": "metadata"}

    id           = Column(BigInteger, primary_key=True, autoincrement=True)
    oid          = Column(BigInteger, nullable=False)
    public_id    = Column(UUID(as_uuid=True), nullable=False, server_default=func.uuid_generate_v4(), unique=True)
    database_id  = Column(BigInteger, ForeignKey("metadata.database.id", ondelete="CASCADE"), nullable=False)
    schema_name  = Column(Text, nullable=False)
    name         = Column(Text, nullable=False)
    description  = Column(Text, nullable=True)
    created_by   = Column(BigInteger, nullable=True)
    created_at   = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_by   = Column(BigInteger, nullable=True)
    updated_at   = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    deleted_by   = Column(BigInteger, nullable=True)
    deleted_at   = Column(DateTime(timezone=True), nullable=True)
