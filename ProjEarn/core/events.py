import datetime
import time
import requests
from threading import Thread
from config import MODEL_NAME, OLLAMA_URL, EVENT_EXTRACT_PROMPT
from utils.messaging import send_whatsapp
from core.store import store

# No local cache or loading needed, Store handles it.

def add_event(user_id, title, event_time):
    """
    event_time should be ISO format string
    """
    event = {
        "user_id": user_id,
        "title": title,
        "time": event_time,
        "notified": False,
        "notified_at": None
    }
    store.add_event(event)
    print(f"📌 Event recorded: '{title}' for {event_time}")
    return event

def run_events_check():
    """Checks and triggers due events. Returns number of triggered items."""
    now_iso = datetime.datetime.now().isoformat()
    triggered_count = 0
    updated = False
    
    # Read fresh copy
    current_events = store.events
    
    for e in current_events:
        if not e["notified"] and e["time"] <= now_iso:
            e["notified"] = True
            e["notified_at"] = now_iso
            msg = f"📅 EVENT NOTIFICATION: {e['title']}"
            send_whatsapp(e["user_id"], msg)
            print(f"🔔 Event notification triggered for {e['user_id']}: {e['title']}")
            triggered_count += 1
            updated = True
        
    if updated:
        store.update_events(current_events)
            
    return triggered_count
    return triggered_count

def check_events_loop():
    """Background loop to check and trigger event notifications."""
    while True:
        run_events_check()
        time.sleep(15) 

def start_event_scheduler():
    Thread(target=check_events_loop, daemon=True).start()

# --- LLM Extraction Logic for Events ---

# Prompt now loaded from config.py

def extract_event_from_text(text):
    """Asks LLM if there's an event in the text and extracts details."""
    try:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt = EVENT_EXTRACT_PROMPT.format(now=now, text=text)
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
            if data.get("is_event"):
                return data
    except Exception as e:
        print(f"⚠️ Event extraction error: {e}")
    return None
