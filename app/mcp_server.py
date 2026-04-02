import requests
from fastmcp import FastMCP

# 1. Initialize MCP
mcp = FastMCP("Todo_Manager")

# 2. Your FastAPI URL
API_URL = "http://127.0.0.1:8000/todos"

@mcp.tool()
def add_todo(title: str, description: str = "", urgency: str = "important", category: str = "Work"):
    """Adds a task to the todo list. Urgency: very important, important, or can do later."""
    payload = {"title": title, "description": description, "urgency": urgency, "category": category}
    try:
        response = requests.post(API_URL, json=payload)
        if response.status_code != 200:
            return f"Error from API (Status {response.status_code}): {response.text}"
        return f"Successfully saved to database: {title}"
    except Exception as e:
        return f"Connection Error: {str(e)}"

@mcp.tool()
def list_tasks():
    """Shows all tasks from the database."""
    response = requests.get(API_URL)
    return response.json()

@mcp.tool()
def update_todo_status(todo_id: int, completed: bool):
    """
    Updates a task's completion status. 
    Use this to mark a task as finished (True) or not finished (False).
    """
    try:
        # Get current task data first
        current = requests.get(f"{API_URL}/{todo_id}").json()
        payload = {
            "title": current["title"],
            "description": current["description"],
            "urgency": current["urgency"],
            "completed": completed
        }
        response = requests.put(f"{API_URL}/{todo_id}", json=payload)
        return f"Updated task {todo_id} to completed={completed}"
    except Exception as e:
        return f"Update Error: {str(e)}"

@mcp.tool()
def search_tasks_by_meaning(query: str):
    """Search for tasks using semantic meaning (RAG). Useful for broad questions."""
    response = requests.get(f"{API_URL}/search", params={"query": query})
    return response.json()

@mcp.tool()
def get_productivity_summary(time_period: str = "today"):
    """Retrieves tasks from a period (today, week, month) to summarize activity."""
    response = requests.get(f"{API_URL}/history", params={"period": time_period})
    return response.json()

if __name__ == "__main__":
    mcp.run()

@mcp.tool()
def send_tasks_to_my_phone():
    """
    Sends the current list of incomplete tasks to the user's Telegram account.
    """
    try:
        response = requests.get(f"{API_URL}/telegram-summary")
        return "I've sent your current task list to your Telegram! Check your phone. 📱"
    except Exception as e:
        return f"Error: {str(e)}"