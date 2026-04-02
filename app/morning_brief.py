import os
import requests
from google import genai
from dotenv import load_dotenv

# Load .env
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(base_dir, "..", ".env"))

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_notion_tasks():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    res = requests.post(url, headers=headers).json()
    task_list = []
    for page in res.get("results", []):
        try:
            name = page["properties"]["Task name"]["title"][0]["text"]["content"]
            status = page["properties"]["Status"]["status"]["name"]
            if status != "Done":
                task_list.append(name)
        except: continue
    return task_list

def get_ai_brief(tasks_list):
    client = genai.Client(api_key=GEMINI_API_KEY)
    tasks_text = "\n".join(tasks_list)
    
    prompt = f"""
    Act as a professional assistant for Amogh. 
    Here is his study schedule from Notion:
    {tasks_text}
    
    Give a smart, 3-sentence motivating morning brief. 
    Tell him exactly what he needs to focus on today to stay on track.
    """
    
    try:
        # Use 'gemini-2.0-flash' - this worked for us in FastAPI
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt
        )
        return response.text
    except Exception as e:
        # If it still fails, we print the real error to the terminal
        print(f"❌ AI brain error: {e}")
        return None
    
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    print("Fetching tasks...")
    tasks = get_notion_tasks()
    
    if tasks:
        print("Attempting AI Summary...")
        brief = get_ai_brief(tasks)
        
        if brief:
            final_msg = f"🌅 *Good Morning Amogh!*\n\n{brief}"
        else:
            # FALLBACK: If AI is exhausted, send the raw list instead of failing
            raw_list = "\n- ".join(tasks)
            final_msg = f"🌅 *Good Morning Amogh!*\n\nGemini is resting, but here are your tasks:\n- {raw_list}"
            
        print("Sending to Telegram...")
        send_telegram(final_msg)
        print("🎉 Done!")
    else:
        print("📭 No tasks found.")