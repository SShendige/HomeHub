import datetime
import requests
from config import MODEL_NAME, OLLAMA_URL, HABIT_EXTRACT_PROMPT
from core.store import store

# No local cache or loading needed, Store handles it.

def log_habit_completion(user_id, habit_name):
    """Logs a completion for a habit and updates streak."""
    today = datetime.date.today().isoformat()
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    
    today = datetime.date.today().isoformat()
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    
    # Read fresh copy
    current_habits = store.habits
    
    # Find existing habit for this user
    habit = next((h for h in current_habits if h["user_id"] == user_id and h["habit"].lower() == habit_name.lower()), None)
    
    if not habit:
        # New habit
        habit = {
            "user_id": user_id,
            "habit": habit_name,
            "last_done": today,
            "streak": 1,
            "total": 1
        }
        current_habits.append(habit)
        status = "new"
    else:
        if habit["last_done"] == today:
            status = "already_done"
        else:
            if habit["last_done"] == yesterday:
                habit["streak"] += 1
            else:
                habit["streak"] = 1 # Reset streak
            
            habit["last_done"] = today
            habit["total"] += 1
            status = "updated"
    
    store.update_habits(current_habits)
    return habit, status

# --- LLM Extraction Logic for Habits ---

# Prompt now loaded from config.py

def extract_habit_from_text(text):
    """Asks LLM if there's a habit completion in the text."""
    try:
        prompt = HABIT_EXTRACT_PROMPT.format(text=text)
        payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
        
        r = requests.post(OLLAMA_URL, json=payload, timeout=30)
        if r.status_code == 200:
            result = r.json().get("response", "").strip()
            # Extract the FIRST JSON object found
            start = result.find("{")
            if start != -1:
                depth = 0
                for i in range(start, len(result)):
                    if result[i] == "{":
                        depth += 1
                    elif result[i] == "}":
                        depth -= 1
                        if depth == 0:
                            result = result[start:i+1]
                            break
            
            data = json.loads(result)
            if data.get("is_completion"):
                return data
    except Exception as e:
        print(f"⚠️ Habit extraction error: {e}")
    return None
