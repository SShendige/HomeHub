import json
import requests
import sys
import datetime 
import traceback
from config import OLLAMA_URL, MODEL_NAME, SYS_PROMPT
from core.memory import ContextManager
from core.sentiment import get_mood

from core.reminders import add_reminder
from core.events import add_event
from core.habits import log_habit_completion
from core.intent import extract_intent

def generate_reply(user_text: str, user_number: str, update_stats_callback=None) -> str:
    """Generate a reply with unified intent extraction (Reminder/Event/Habit/Chat)."""
    try:
        ctx_mgr = ContextManager(user_number)
        history_text = ctx_mgr.get_prompt_context()
        facts_text = ctx_mgr.get_facts_summary()
        
        now = datetime.datetime.now()
        timestamp_str = now.strftime("%A, %d %B %Y, %I:%M %p")
        mood = get_mood(user_text)
        
        if update_stats_callback:
            update_stats_callback(user_number, mood)

        # Unified Intent Extraction
        intent_data = extract_intent(user_text, history=history_text)
        intent = intent_data.get("intent", "chat")
        
        # Action logic
        status_note = ""
        if intent == "reminder":
            add_reminder(user_number, intent_data["task_title"], intent_data["time"])
            status_note = f"Reminder set for {intent_data['time']}"
        elif intent == "event":
            add_event(user_number, intent_data["task_title"], intent_data["time"])
            status_note = f"Event recorded for {intent_data['time']}"
        elif intent == "habit":
            habit, _ = log_habit_completion(user_number, intent_data["task_title"])
            status_note = f"Habit '{habit['habit']}' tracked (Streak: {habit['streak']})"
        
        if status_note:
            print(f"📡 [INTERNAL] {status_note}")

        prompt = (
            f"{SYS_PROMPT}\n"
            f"Current Time: {timestamp_str}\n"
            f"Known facts about User:\n{facts_text}\n\n"
            f"Context: User is currently feeling {mood}. Their message intent: {intent}.\n"
            f"--- CONVERSATION HISTORY ---\n"
            f"{history_text}\n"
            f"--- NEW MESSAGE ---\n"
            f"User: {user_text}\n"
            f"HomeHub:"
        )

        payload = {"model": MODEL_NAME, "prompt": prompt}

        with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120) as r:
            reply_chunks = []
            for line in r.iter_lines():
                if not line: continue
                data = json.loads(line.decode("utf-8"))
                if "response" in data:
                    reply_chunks.append(data["response"])
                if data.get("done", False):
                    break

        reply = "".join(reply_chunks).strip() or "I'm not sure how to respond right now."
        
        ctx_mgr.add_turn(user_text, reply)
        return reply

    except Exception as e:
        traceback.print_exc()
        return "⚠️ Sorry, I had trouble responding this time."
