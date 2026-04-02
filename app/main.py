import os
import requests
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from . import schemas, crud, models
from google import genai
from pgvector.sqlalchemy import Vector
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

# --- CONFIG ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB_ID = os.getenv("NOTION_DATABASE_ID")

# Initialize the NEW Gemini Client
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize Database Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Pro AI Agent OS")

# --- HELPER FUNCTIONS ---

def get_embedding(text: str):
    """
    Turns text into a 768-dimension vector.
    Fixes the 404 by using the stable string name.
    """
    try:
        # Trying the most basic name first
        result = gemini_client.models.embed_content(
            model="text-embedding-004", 
            contents=text
        )
        return result.embeddings[0].values
    except Exception as e:
        print(f"⚠️ Embedding API Error: {e}")
        # Try one last fallback to the original model
        try:
            result = gemini_client.models.embed_content(model="embedding-001", contents=text)
            return result.embeddings[0].values
        except:
            return [0.0] * 768

def sync_to_notion(title: str, urgency: str, category: str, description: str = ""):
    """Mirrors the task to Notion. Fixes the multi_select error."""
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    priority_map = {"very important": "High", "important": "Medium", "can do later": "Low"}
    notion_priority = priority_map.get(urgency.lower(), "Medium")
    notion_category = category.title() if category else "General"

    # FIX: We change 'select' to 'multi_select' and put the category in a list []
    data = {
        "parent": { "database_id": NOTION_DB_ID },
        "properties": {
            "Task name": { "title": [{"text": {"content": title}}] },
            "Priority": { "select": {"name": notion_priority} },
            "Task type": { 
                "multi_select": [{"name": notion_category}] 
            },
            "Description": { "rich_text": [{"text": {"content": description or ""}}] },
            "Status": { "status": {"name": "Not started"} }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print(f"✅ Synced to Notion! Category: {notion_category}")
        else:
            print(f"❌ Notion API Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Notion Connection Error: {e}")

# --- ROUTES ---

@app.post("/todos", response_model=schemas.Todo)
def create(todo: schemas.TodoCreate, db: Session = Depends(get_db)):
    # 1. Generate Vector Meaning
    vector = get_embedding(todo.title)
    
    # 2. Save to Postgres
    todo_data = todo.model_dump() if hasattr(todo, "model_dump") else todo.dict()
    db_todo = models.Todo(**todo_data, embedding=vector)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    
    # 3. Sync to Notion
    if NOTION_TOKEN and NOTION_DB_ID:
        try:
            sync_to_notion(todo.title, todo.urgency, db_todo.category, todo.description)
        except Exception as e:
            print(f"Notion Sync Error: {e}")
            
    return db_todo

@app.get("/todos/search")
def search_tasks(query: str, db: Session = Depends(get_db)):
    """RAG Semantic Search."""
    query_vector = get_embedding(query)
    results = db.query(models.Todo).order_by(
        models.Todo.embedding.cosine_distance(query_vector)
    ).limit(5).all()
    return results

@app.get("/todos/telegram-summary")
def send_summary_to_telegram(db: Session = Depends(get_db)):
    """Triggers the manual Telegram push."""
    tasks = db.query(models.Todo).filter(models.Todo.completed == False).all()
    if not tasks:
        send_telegram_msg("✅ No pending tasks!")
        return {"status": "Empty list sent"}
    
    msg = "🚀 *Your Pending Tasks*:\n\n"
    for t in tasks:
        icon = "🔴" if t.urgency == "very important" else "🟡"
        msg += f"{icon} *{t.title}*\n"
    
    send_telegram_msg(msg)
    return {"status": "Sent"}

@app.get("/todos/history")
def get_history(period: str = "today", db: Session = Depends(get_db)):
    """Used for the Productivity Summary feature."""
    now = datetime.now(timezone.utc)
    if period == "week": start_date = now - timedelta(days=7)
    elif period == "month": start_date = now - timedelta(days=30)
    else: start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

    return db.query(models.Todo).filter(models.Todo.created_at >= start_date).all()

# --- STANDARD CRUD ---
@app.get("/todos", response_model=list[schemas.Todo])
def read_all(db: Session = Depends(get_db)):
    return crud.get_todos(db)

@app.get("/todos/{todo_id}", response_model=schemas.Todo)
def read_one(todo_id: int, db: Session = Depends(get_db)):
    todo = crud.get_todo(db, todo_id)
    if not todo: raise HTTPException(status_code=404, detail="Not found")
    return todo

@app.put("/todos/{todo_id}", response_model=schemas.Todo)
def update(todo_id: int, todo: schemas.TodoCreate, db: Session = Depends(get_db)):
    return crud.update_todo(db, todo_id, todo)

@app.delete("/todos/{todo_id}")
def delete(todo_id: int, db: Session = Depends(get_db)):
    crud.delete_todo(db, todo_id)
    return {"message": "Deleted"}

@app.get("/", include_in_schema=False)
def root(): return RedirectResponse(url="/docs")