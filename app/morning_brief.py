import os, requests
from dotenv import load_dotenv

load_dotenv()

def send_brief():
    # 1. Get tasks from Notion
    url = f"https://api.notion.com/v1/databases/{os.getenv('NOTION_DATABASE_ID')}/query"
    headers = {
        "Authorization": f"Bearer {os.getenv('NOTION_TOKEN')}",
        "Notion-Version": "2022-06-28"
    }
    res = requests.post(url, headers=headers).json()
    
    tasks = []
    for page in res.get("results", []):
        name = page["properties"]["Task name"]["title"][0]["text"]["content"]
        status = page["properties"]["Status"]["status"]["name"]
        if status != "Done":
            tasks.append(name)

    # 2. Format and send to Telegram
    if tasks:
        msg = "🌅 *Good Morning, Amogh!*\n\nHere are your pending tasks:\n- " + "\n- ".join(tasks)
        tel_url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}/sendMessage"
        requests.post(tel_url, json={"chat_id": os.getenv("CHAT_ID"), "text": msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    send_brief()