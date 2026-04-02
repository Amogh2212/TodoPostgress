from sqlalchemy import Column, Integer, String, Boolean, DateTime
from pgvector.sqlalchemy import Vector # Import this
from .database import Base
from sqlalchemy.sql import func

class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    completed = Column(Boolean, default=False)
    urgency = Column(String)
    embedding = Column(Vector(768))
    # Add these two:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    category = Column(String, default="General")
