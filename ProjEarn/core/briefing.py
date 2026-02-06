import datetime
import requests
import json
from config import MODEL_NAME, OLLAMA_URL, BRIEFING_PROMPT, DEFAULT_CITY, DEFAULT_WAKE_TIME
from core.store import store
from core.memory import user_facts
from utils.messaging import send_whatsapp

def get_weather(city=DEFAULT_CITY):
    """Fetches simple weather info from Open-Meteo (free, no key)."""
    try:
        # We'll use Bengaluru coordinates as default if city is Bengaluru
        lat, lon = 12.9716, 77.5946 # Bengaluru
        
        # In a real app, we'd geocode the city name. 
        # For now, let's just use default or placeholder.
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json().get("current_weather", {})
            temp = data.get("temperature")
            wind = data.get("windspeed")
            return f"{temp}°C with wind speed of {wind}km/h"
    except Exception as e:
        print(f"⚠️ Weather fetch failed: {e}")
    return "Weather data unavailable"

def get_today_agenda(user_id):
    """Gathers events and reminders for the current day."""
    today = datetime.date.today().isoformat()
    
    # Use store accessors for thread-safe reads
    current_reminders = store.reminders
    current_events = store.events
    
    # Filter reminders for today (or already passed but not notified)
    today_reminders = [r["task"] for r in current_reminders if r["user_id"] == user_id and r["time"].startswith(today)]
    
    # Filter events for today
    today_events = [e["title"] for e in current_events if e["user_id"] == user_id and e["time"].startswith(today)]
    
    rem_str = ", ".join(today_reminders) if today_reminders else "None"
    evt_str = ", ".join(today_events) if today_events else "None"
    
    return evt_str, rem_str

def generate_morning_briefing(user_id):
    """Generates and sends the daily briefing."""
    city = DEFAULT_CITY
    # Check if we know user's location from facts
    facts = user_facts.get(user_id, [])
    for f in facts:
        if "location:" in f.lower() or "city:" in f.lower():
            city = f.split(":")[-1].strip()
            break
            
    weather = get_weather(city)
    events_list, reminders_list = get_today_agenda(user_id)
    
    date_str = datetime.date.today().strftime("%A, %d %B %Y")
    
    prompt = BRIEFING_PROMPT.format(
        date=date_str,
        city=city,
        weather=weather,
        events=events_list,
        reminders=reminders_list
    )
    
    try:
        payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
        r = requests.post(OLLAMA_URL, json=payload, timeout=60)
        if r.status_code == 200:
            briefing = r.json().get("response", "").strip()
            if briefing:
                send_whatsapp(user_id, f"☀️ *Good Morning! Here is your Daily Briefing* ☀️\n\n{briefing}")
                print(f"✅ Briefing sent to {user_id}")
                return True
    except Exception as e:
        print(f"⚠️ Briefing generation failed: {e}")
    return False

# We need a way to track if briefing was sent today per user
briefings_sent = {} # {user_id: "YYYY-MM-DD"}

def check_and_send_briefings():
    """Checks if it's wake-up time for users and sends briefing."""
    global briefings_sent
    now = datetime.datetime.now()
    today_str = now.date().isoformat()
    current_time_str = now.strftime("%H:%M")
    
    # In a real multi-user system, we'd iterate over all active users.
    # For now, we'll check users in user_facts.
    for user_id in user_facts.keys():
        if briefings_sent.get(user_id) == today_str:
            continue
            
        # Determine wake time: check facts or use default
        wake_time = DEFAULT_WAKE_TIME
        facts = user_facts.get(user_id, [])
        for f in facts:
            if "wake" in f.lower() and "time:" in f.lower():
                # Extract time using simple split
                try:
                    wake_time = f.split(":")[-1].strip()
                except: pass
                break
        
        # If it's time to wake up (or past it), send briefing
        if current_time_str >= wake_time:
            if generate_morning_briefing(user_id):
                briefings_sent[user_id] = today_str
