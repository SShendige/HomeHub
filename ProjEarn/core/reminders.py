import datetime
import time
import requests
from threading import Thread
from config import MODEL_NAME, OLLAMA_URL, REMINDER_EXTRACT_PROMPT
from utils.messaging import send_whatsapp
from core.store import store

# No local cache or loading needed, Store handles it.

def add_reminder(user_id, task, reminder_time):
    """
    reminder_time should be ISO format string
    """
    reminder = {
        "user_id": user_id,
        "task": task,
        "time": reminder_time,
        "notified": False,
        "notified_at": None
    }
    store.add_reminder(reminder)
    print(f"📌 Reminder added: '{task}' for {reminder_time}")
    return reminder

def run_reminders_check():
    """Checks and triggers due reminders. Returns number of triggered items."""
    today_iso = datetime.datetime.now().isoformat()
    triggered_count = 0
    updated = False
    
    # Read fresh copy
    current_reminders = store.reminders
    
    for r in current_reminders:
        if not r["notified"] and r["time"] <= today_iso:
            r["notified"] = True
            r["notified_at"] = today_iso
            msg = f"⏰ REMINDER: {r['task']}"
            send_whatsapp(r["user_id"], msg)
            print(f"🔔 Reminder triggered for {r['user_id']}: {r['task']}")
            triggered_count += 1
            updated = True
            
    if updated:
        # Atomic commit back to store
        store.update_reminders(current_reminders)
            
    return triggered_count

def check_reminders_loop():
    """Background loop to check and trigger reminders."""
    while True:
        run_reminders_check()
        time.sleep(10) # check every 10 seconds

def start_reminder_scheduler():
    Thread(target=check_reminders_loop, daemon=True).start()

# --- LLM Extraction Logic for Reminders ---

# Prompt now loaded from config.py

def extract_reminder_from_text(text):
    """Asks LLM if there's a reminder in the text and extracts details."""
    try:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt = REMINDER_EXTRACT_PROMPT.format(now=now, text=text)
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
            if data.get("is_reminder"):
                return data
    except Exception as e:
        print(f"⚠️ Reminder extraction error: {e}")
    return None
