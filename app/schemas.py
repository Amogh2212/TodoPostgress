from pydantic import BaseModel

class TodoBase(BaseModel):
    title: str
    description: str | None = None
    completed: bool = False
    urgency: str = "can do later"  # NEW

class TodoCreate(TodoBase):
    pass

class Todo(TodoBase):
    id: int

    class Config:
        from_attributes = True
