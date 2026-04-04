import os
import requests
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models

load_dotenv()

# --- CONFIG ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
USER_NAME = os.getenv("USER_NAME", "User")


def get_tasks_from_db():
    """Fetches all incomplete tasks from PostgreSQL, grouped by urgency."""
    db: Session = SessionLocal()
    try:
        todos = (
            db.query(models.Todo)
            .filter(models.Todo.completed == False)
            .order_by(models.Todo.urgency)
            .all()
        )
        return todos
    finally:
        db.close()


def build_task_sections(todos):
    """Groups tasks into urgency buckets for the prompt."""
    buckets = {
        "very important": [],
        "important": [],
        "can do later": [],
    }
    for t in todos:
        key = t.urgency.lower() if t.urgency else "can do later"
        buckets.setdefault(key, []).append(f"- {t.title}" + (f" ({t.category})" if t.category else ""))
    return buckets


def get_groq_summary(buckets: dict) -> str:
    """Sends the task list to Groq and returns an AI-generated summary."""
    if not GROQ_API_KEY:
        # Fallback: plain text summary without AI
        lines = [f"🔴 *Critical*"] + buckets.get("very important", ["None"]) + \
                ["\n🟡 *Important*"] + buckets.get("important", ["None"]) + \
                ["\n🟢 *Later*"] + buckets.get("can do later", ["None"])
        return "\n".join(lines)

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    critical = "\n".join(buckets.get("very important", [])) or "None"
    normal   = "\n".join(buckets.get("important", []))       or "None"
    later    = "\n".join(buckets.get("can do later", []))    or "None"

    prompt = f"""
You are {USER_NAME}'s elite productivity assistant giving a morning briefing.

Here are all pending tasks grouped by priority:

🔴 CRITICAL (very important):
{critical}

🟡 IMPORTANT:
{normal}

🟢 CAN DO LATER:
{later}

INSTRUCTIONS:
1. Acknowledge every task listed — do not skip any.
2. Suggest a smart order to tackle them today.
3. Keep tone high-energy and motivating.
4. Use Markdown and Emojis.
5. Keep total response under 180 words.
"""

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that never omits tasks."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5
    }

    try:
        response = requests.post(url, headers=headers, json=data).json()
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ AI Error: {e}\n\nCritical: {critical}"


def send_telegram(text: str):
    """Sends a message to the configured Telegram chat."""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️  Telegram not configured (TELEGRAM_TOKEN / CHAT_ID missing). Printing instead:\n")
        print(text)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    print("✅ Morning brief sent to Telegram!")


if __name__ == "__main__":
    print("📋 Fetching tasks from database...")
    todos = get_tasks_from_db()

    if not todos:
        send_telegram(
            f"🌅 *Good Morning {USER_NAME}!*\n\n"
            "Your task list is completely clear. Great time to plan something new! ☕"
        )
    else:
        print(f"   Found {len(todos)} pending task(s).")
        buckets = build_task_sections(todos)

        print("🤖 Generating AI summary...")
        summary = get_groq_summary(buckets)

        print("📱 Sending to Telegram...")
        send_telegram(f"🌅 *Morning Brief for {USER_NAME}*\n\n{summary}")