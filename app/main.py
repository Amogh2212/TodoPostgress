from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from . import schemas, crud, models
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def root():
    return {"message": "ToDo API is running!"}

@app.post("/todos", response_model=schemas.Todo)
def create(todo: schemas.TodoCreate, db: Session = Depends(get_db)):
    return crud.create_todo(db, todo)

@app.get("/todos", response_model=list[schemas.Todo])
def read_all(db: Session = Depends(get_db)):
    return crud.get_todos(db)

@app.get("/todos/next-task")
def get_next_todo(db: Session = Depends(get_db)):
    todos = crud.get_todos(db)
    if not todos:
        raise HTTPException(status_code=404, detail="No todos found")

    # Build a simple prompt with urgency info
    items_text = "\n".join(
        f"- title: {t.title}, description: {t.description}, urgency: {t.urgency}"
        for t in todos
    )

    prompt = f"""
You are a productivity assistant.

Here is the todo list, each with an urgency of 'very important', 'important', or 'can do later':

{items_text}

Pick exactly ONE task that the user should do next.
Return a short one-line answer in this format:

Do: <title> - <short reason>
"""

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt
    )
    return {"recommendation": response.text.strip()}

@app.get("/todos/{todo_id}", response_model=schemas.Todo)
def read_one(todo_id: int, db: Session = Depends(get_db)):
    todo = crud.get_todo(db, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@app.put("/todos/{todo_id}", response_model=schemas.Todo)
def update(todo_id: int, todo: schemas.TodoCreate, db: Session = Depends(get_db)):
    updated = crud.update_todo(db, todo_id, todo)
    if not updated:
        raise HTTPException(status_code=404, detail="Todo not found")
    return updated

@app.delete("/todos/{todo_id}")
def delete(todo_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_todo(db, todo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"message": "Deleted successfully"}

