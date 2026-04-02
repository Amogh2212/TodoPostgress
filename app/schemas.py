from pydantic import BaseModel
from typing import Optional

class TodoBase(BaseModel):
    title: str
    description: str | None = None
    completed: bool = False
    urgency: str = "can do later" 
    category: Optional[str] = "General"

class TodoCreate(TodoBase):
    pass

class Todo(TodoBase):
    id: int

    class Config:
        from_attributes = True
