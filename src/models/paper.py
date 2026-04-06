import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID 
from sqlalchemy.sql import func

from src.db.interface.postgresql import Base


class Paper(Base):
    __tablename__ = "papers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    arxive_id = Column(String, nullable=False, unique=True, index=True)
    title = Column(String, nullable=False)
    abstract = Column(Text, nullable=False)
    authors = Column(JSON, nullable=False)
    published_date = Column(DateTime, nullable=False)
    pdf_url = Column(String, nullable=False)
    categories = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))