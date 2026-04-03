import os
import requests
from datetime import datetime, timedelta, date
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def get_tasks_from_notion():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    # Calculate dates for Today and Tomorrow
    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    
    # Filter: Status is not Done AND (Date is Today OR Date is Tomorrow)
    query_filter = {
        "filter": {
            "and": [
                { "property": "Status", "status": { "does_not_equal": "Done" } },
                {
                    "or": [
                        { "property": "Due date", "date": { "equals": today } },
                        { "property": "Due date", "date": { "equals": tomorrow } }
                    ]
                }
            ]
        }
    }
    
    res = requests.post(url, headers=headers, json=query_filter).json()
    
    today_tasks = []
    tomorrow_tasks = []

    for page in res.get("results", []):
        try:
            title = page["properties"]["Task name"]["title"][0]["text"]["content"]
            due_date = page["properties"]["Due date"]["date"]["start"]
            urgency = page["properties"]["Priority"]["select"]["name"]
            
            task_info = f"- {title} ({urgency})"
            if due_date == today:
                today_tasks.append(task_info)
            else:
                tomorrow_tasks.append(task_info)
        except (KeyError, TypeError):
            continue
            
    return today_tasks, tomorrow_tasks

def get_groq_summary(today_list, tomorrow_list):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt_text = f"""
    You are Amogh's elite productivity assistant. 
    Here are the tasks for the next 48 hours:
    TODAY:
    {chr(10).join(today_list) if today_list else "No tasks today."}
    
    TOMORROW:
    {chr(10).join(tomorrow_list) if tomorrow_list else "No tasks tomorrow."}

    Write a high-energy, very short morning brief (max 120 words). 
    1. Highlight the single most important task for today.
    2. Give a quick overview of what's coming tomorrow.
    3. End with a 1-sentence motivation.
    Use Markdown with emojis.
    """
    
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a concise, helpful productivity coach."},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=data).json()
        return response['choices'][0]['message']['content']
    except Exception as e:
        return "⚠️ AI summary failed, but you have tasks! Check your Notion board."

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    print("Checking Notion...")
    t_today, t_tomorrow = get_tasks_from_notion()
    
    if not t_today and not t_tomorrow:
        send_telegram("🌅 *Good Morning Amogh!*\n\nYour schedule is clear for today and tomorrow. Time to relax or work on something new! ☕")
    else:
        print("Generating Groq summary...")
        summary = get_groq_summary(t_today, t_tomorrow)
        print("Sending to Telegram...")
        send_telegram(f"🌅 *Morning Brief for Amogh*\n\n{summary}")