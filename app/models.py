from sqlalchemy import Column, Integer, String, Boolean  # already there

from .database import Base

class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False)
    urgency = Column(String, nullable=False, default="can do later")  # NEW
