from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from . import schemas, crud, models
import os
from dotenv import load_dotenv
from fastapi.responses import RedirectResponse
from google import genai
from pgvector.sqlalchemy import Vector
from datetime import datetime, timedelta, timezone
import requests
from apscheduler.schedulers.background import BackgroundScheduler

# Load environment variables
load_dotenv()

# 1. Initialize the NEW Gemini Client (Handles both Chat and Embeddings)
gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Initialize Database Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Todo List AI Agent API",
    description="API for managing a todo list with AI-powered task prioritization and RAG search.",
    version="2.0.0"
)

# --- HELPER FUNCTIONS ---

def get_embedding(text: str):
    """
    Turns text into a 768-dimension vector using Gemini.
    """
    try:
        # We use text-embedding-004 which is the latest stable version
        result = gemini_client.models.embed_content(
            model="text-embedding-004", 
            contents=text
        )
        return result.embeddings[0].values
    except Exception as e:
        print(f"Embedding Error: {e}")
        # Fallback to a zero-vector so the database doesn't crash 
        # (768 zeros for Gemini embeddings)
        return [0.0] * 768

# --- ROUTES ---

@app.get("/", include_in_schema=False)
def root():
    """Redirects to the API documentation."""
    return RedirectResponse(url="/docs")

@app.post("/todos", response_model=schemas.Todo, summary="Create a new task with RAG")
def create(todo: schemas.TodoCreate, db: Session = Depends(get_db)):
    """
    Adds a new task and generates a semantic embedding for RAG search.
    """
    # Generate the vector meaning of the title
    vector = get_embedding(todo.title)
    
    # Create the database object with the embedding
    # We use model_dump() (Pydantic v2) or dict() (Pydantic v1)
    todo_data = todo.model_dump() if hasattr(todo, "model_dump") else todo.dict()
    db_todo = models.Todo(**todo_data, embedding=vector)
    
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.get("/todos/search", summary="Search tasks by meaning (RAG)")
def search_tasks(query: str, db: Session = Depends(get_db)):
    """
    Retrieval-Augmented Generation (RAG) tool.
    Finds the 5 most semantically similar tasks based on the user's query.
    """
    query_vector = get_embedding(query)
    
    # Cosine distance search using pgvector
    results = db.query(models.Todo).order_by(
        models.Todo.embedding.cosine_distance(query_vector)
    ).limit(5).all()
    
    return results

@app.get("/todos", response_model=list[schemas.Todo], summary="List all tasks")
def read_all(db: Session = Depends(get_db)):
    """Fetches every task currently stored in the database."""
    return crud.get_todos(db)

@app.get("/todos/next-task", summary="Get AI recommendation for next task")
def get_next_todo(db: Session = Depends(get_db)):
    """
    Uses Gemini to analyze all tasks and recommend exactly ONE task 
    the user should focus on next.
    """
    todos = crud.get_todos(db)
    if not todos:
        raise HTTPException(status_code=404, detail="No todos found")

    items_text = "\n".join(
        f"- title: {t.title}, description: {t.description}, urgency: {t.urgency}"
        for t in todos
    )

    prompt = f"""
    You are a productivity assistant.
    Here is the todo list, each with an urgency level:
    {items_text}

    Pick exactly ONE task that the user should do next.
    Return a short one-line answer in this format:
    Do: <title> - <short reason>
    """

    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=prompt
    )
    return {"recommendation": response.text.strip()}

@app.get("/todos/{todo_id}", response_model=schemas.Todo, summary="Get a specific task by ID")
def read_one(todo_id: int, db: Session = Depends(get_db)):
    """Retrieves details of a single task using its unique ID."""
    todo = crud.get_todo(db, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@app.put("/todos/{todo_id}", response_model=schemas.Todo, summary="Update an existing task")
def update(todo_id: int, todo: schemas.TodoCreate, db: Session = Depends(get_db)):
    """
    Updates the title, description, or urgency of an existing task.
    """
    updated = crud.update_todo(db, todo_id, todo)
    if not updated:
        raise HTTPException(status_code=404, detail="Todo not found")
    return updated

@app.delete("/todos/{todo_id}", summary="Delete a task")
def delete(todo_id: int, db: Session = Depends(get_db)):
    """Permanently removes a task from the database."""
    deleted = crud.delete_todo(db, todo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"message": f"Task {todo_id} deleted successfully"}

@app.get("/todos/history", summary="Get tasks for a specific time range")
def get_history(period: str = "today", db: Session = Depends(get_db)):
    """
    period can be: 'today', 'week', or 'month'
    """
    now = datetime.now(timezone.utc)
    
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Fetch tasks created or completed in this window
    tasks = db.query(models.Todo).filter(
        (models.Todo.created_at >= start_date) | 
        (models.Todo.completed_at >= start_date)
    ).all()
    
    return tasks

def send_telegram_msg(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        # ADD THIS LINE TO DEBUG:
        print(f"Telegram API Response: {response.json()}") 
    except Exception as e:
        print(f"Telegram Error: {e}")

# New API endpoint to trigger the Telegram summary
@app.get("/todos/telegram-summary", summary="Send summary to Telegram")
def send_summary_to_telegram(db: Session = Depends(get_db)):
    # 1. Fetch incomplete tasks
    tasks = db.query(models.Todo).filter(models.Todo.completed == False).all()
    
    if not tasks:
        send_telegram_msg("✅ *All clear!* You have no pending tasks in your todo list.")
        return {"status": "Empty list sent"}

    # 2. Format the message with emojis
    msg = "🚀 *Pending Tasks for Amogh*:\n\n"
    for t in tasks:
        icon = "🔴" if t.urgency == "very important" else "🟡"
        msg += f"{icon} *{t.title}*\n   _{t.urgency}_\n\n"
    
    # 3. Send to phone
    send_telegram_msg(msg)
    return {"status": "Summary sent to Telegram"}

@app.on_event("startup")
def start_scheduler():
    scheduler = BackgroundScheduler()
    # Change 'telegram_summary' to 'send_summary_to_telegram'
    scheduler.add_job(
        lambda: send_summary_to_telegram(next(get_db())), 
        'cron', 
        hour=8, 
        minute=00
    )
    scheduler.start()