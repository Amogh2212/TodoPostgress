import os
import requests
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from . import schemas, crud, models
from google import genai
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Initialize the Gemini Client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️  WARNING: GEMINI_API_KEY not set. Embedding & AI features will be disabled.")
    gemini_client = None
else:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# --- STARTUP VALIDATION ---
print("\n🔧 Service Configuration Status:")
print(f"   📦 Database:  {'✅ Connected' if os.getenv('DATABASE_URL') else '❌ DATABASE_URL not set!'}")
print(f"   🤖 Gemini:    {'✅ Ready' if GEMINI_API_KEY else '⚠️  Disabled — semantic search will not work'}")
print(f"   📱 Telegram:  {'✅ Ready' if TELEGRAM_TOKEN and CHAT_ID else '⚪ Disabled (set TELEGRAM_TOKEN + CHAT_ID)'}")
print()

# Initialize Database Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Pro AI Agent OS",
    description="A smart To-Do API with Gemini AI, Telegram notifications, and semantic search.",
    version="1.0.0",
)

# --- HELPER FUNCTIONS ---

def send_telegram_msg(text: str):
    """Sends a message to the configured Telegram chat."""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ Telegram not configured. Skipping message.")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

def get_embedding(text: str):
    """Turns text into a 768-dimension vector using Gemini."""
    if not gemini_client:
        return [0.0] * 768
    try:
        result = gemini_client.models.embed_content(
            model="text-embedding-004", 
            contents=text
        )
        return result.embeddings[0].values
    except Exception as e:
        print(f"⚠️ Embedding API Error: {e}")
        try:
            result = gemini_client.models.embed_content(model="embedding-001", contents=text)
            return result.embeddings[0].values
        except:
            return [0.0] * 768

# --- ROUTES ---


@app.post("/todos", response_model=schemas.Todo)
def create(todo: schemas.TodoCreate, db: Session = Depends(get_db)):
    # 1. Generate semantic embedding
    vector = get_embedding(todo.title)

    # 2. Save to Postgres
    todo_data = todo.model_dump()
    db_todo = models.Todo(**todo_data, embedding=vector)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)

    return db_todo

@app.get("/todos/search")
def search_tasks(query: str, db: Session = Depends(get_db)):
    """Semantic search — finds tasks by meaning using vector similarity."""
    if not gemini_client:
        raise HTTPException(
            status_code=503,
            detail="Semantic search is unavailable: GEMINI_API_KEY is not configured."
        )
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