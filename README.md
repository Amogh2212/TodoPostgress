# 🚀 Pro AI Agent OS — Smart Todo API

A backend-only To-Do List application built with **FastAPI** and **PostgreSQL (Neon)**, featuring complete CRUD operations, **Gemini AI**-powered semantic search, **Notion** sync, **Telegram** notifications, and an AI-powered **Morning Brief** system.

## ✨ Features

| Feature | Description |
|---------|-------------|
| **CRUD API** | Full Create, Read, Update, Delete for tasks via REST API |
| **Semantic Search** | Find tasks by meaning using Gemini embeddings + pgvector |
| **Notion Sync** | Auto-mirrors new tasks to a Notion database |
| **Telegram Alerts** | Push pending tasks to your phone via Telegram bot |
| **Morning Brief** | Daily AI-generated task summary sent to Telegram (uses Groq) |
| **MCP Server** | Control your tasks through AI assistants (Claude, etc.) |
| **Smart Categories** | Tasks auto-categorized with urgency levels |

## 🛠️ Tech Stack

- **Framework:** FastAPI + Uvicorn
- **Database:** PostgreSQL (Neon) with pgvector extension
- **AI/ML:** Google Gemini (embeddings), Groq (summaries)
- **Integrations:** Notion API, Telegram Bot API
- **ORM:** SQLAlchemy

---

## 📦 Prerequisites

Before you begin, ensure you have:

1. **Python 3.10+** installed → [Download](https://www.python.org/downloads/)
2. **A PostgreSQL database** with the `pgvector` extension enabled.  
   Recommended: [Neon](https://neon.tech/) (free tier available).  
   Run this SQL in your database:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. **A Google Gemini API key** → [Get one here](https://aistudio.google.com/app/apikey)

### Optional (for extra features):
- **Telegram Bot Token** → Talk to [@BotFather](https://t.me/BotFather) on Telegram
- **Notion Integration Token** → [Create integration](https://www.notion.so/my-integrations)
- **Groq API Key** → [Get one here](https://console.groq.com/keys) (for Morning Brief)

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/Amogh2212/TodoPostgress.git
cd TodoPostgress
```

### 2. Create a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```
Now open `.env` in your editor and fill in your API keys. At minimum, you need:
- `DATABASE_URL` — your PostgreSQL connection string
- `GEMINI_API_KEY` — your Google Gemini API key

> **💡 Tip:** The app works with just these two variables! Telegram, Notion, and Groq features will gracefully disable themselves if their keys aren't set.

### 5. Run the server
```bash
uvicorn app.main:app --reload
```

### 6. Open the API docs
Visit **http://127.0.0.1:8000/docs** in your browser to see the interactive Swagger UI.

On startup, you'll see a status check like this:
```
🔧 Service Configuration Status:
   📦 Database:  ✅ Connected
   🤖 Gemini:    ✅ Ready
   📱 Telegram:  ⚪ Disabled (set TELEGRAM_TOKEN + CHAT_ID)
   📓 Notion:    ⚪ Disabled (set NOTION_TOKEN + NOTION_DATABASE_ID)
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/todos` | Create a new task |
| `GET` | `/todos` | List all tasks |
| `GET` | `/todos/{id}` | Get a specific task |
| `PUT` | `/todos/{id}` | Update a task |
| `DELETE` | `/todos/{id}` | Delete a task |
| `GET` | `/todos/search?query=...` | Semantic search across tasks |
| `GET` | `/todos/telegram-summary` | Send pending tasks to Telegram |
| `GET` | `/todos/history?period=today` | Get task history (today/week/month) |

### Example: Create a Task
```bash
curl -X POST http://127.0.0.1:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn FastAPI", "description": "Complete the tutorial", "urgency": "important", "category": "Learning"}'
```

---

## 🤖 MCP Server (AI Assistant Integration)

The MCP server lets you control your tasks through AI assistants like Claude.

```bash
# Start the MCP server (in a separate terminal)
python -m app.mcp_server
```

Make sure the FastAPI server is running first (`uvicorn app.main:app --reload`).

---

## 🌅 Morning Brief

A standalone script that fetches **all incomplete tasks from PostgreSQL** and sends an AI-generated priority summary to Telegram.

```bash
python -m app.morning_brief
```

**Requires:** `DATABASE_URL`  
**Optional:** `GROQ_API_KEY` (falls back to plain text if missing), `TELEGRAM_TOKEN` + `CHAT_ID` (prints to console if missing)

> Notion is **no longer needed** for the Morning Brief — it reads directly from your database, so it's always in sync.

---

## ⚙️ GitHub Actions — Automated Morning Brief

The workflow at `.github/workflows/morning_brief.yml` runs automatically at **9:00 AM IST every day**.

### Setting up GitHub Secrets

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Required? | Description |
|--------|-----------|-------------|
| `DATABASE_URL` | ✅ Required | Your PostgreSQL connection string |
| `GROQ_API_KEY` | ⚪ Optional | AI-generated summary (plain text fallback if missing) |
| `TELEGRAM_TOKEN` | ⚪ Optional | Telegram bot token (logs to Actions console if missing) |
| `CHAT_ID` | ⚪ Optional | Your Telegram chat ID |
| `USER_NAME` | ⚪ Optional | Your name for the greeting message |

> **Note:** `NOTION_TOKEN` and `NOTION_DATABASE_ID` are **no longer needed** for the morning brief. If you had them set as GitHub Secrets, you can safely delete them.

You can also trigger the workflow manually anytime from the **Actions tab** in your GitHub repo.

---

## 📁 Project Structure

```
TodoPostgress/
├── app/
│   ├── main.py            # FastAPI app, routes, and helper functions
│   ├── database.py        # SQLAlchemy engine and session setup
│   ├── models.py          # Database table definitions
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── crud.py            # Database CRUD operations
│   ├── morning_brief.py   # Standalone morning summary script
│   └── mcp_server.py      # MCP server for AI assistant control
├── .env.example           # Template for environment variables
├── .gitignore
├── requirements.txt       # Python dependencies
└── README.md
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| `FATAL: DATABASE_URL not set` | Copy `.env.example` to `.env` and set your database URL |
| `pgvector extension not found` | Run `CREATE EXTENSION IF NOT EXISTS vector;` in your database |
| `Embedding API Error` | Check your `GEMINI_API_KEY` is valid |
| `Notion API Error 400` | Ensure your Notion database has the correct property names: `Task name`, `Priority`, `Task type`, `Description`, `Status` |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |

---

## 📝 License

This project is for learning purposes.
