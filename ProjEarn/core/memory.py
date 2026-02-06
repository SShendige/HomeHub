import datetime
from threading import RLock, Thread
from collections import defaultdict
import requests
import json
from config import MEMORY_FILE, FACTS_FILE, STATS_FILE, MAX_MEMORY, MODEL_NAME, OLLAMA_URL, FACT_PROMPT
from utils.persistence import load_json, save_json

# Global state
user_contexts = defaultdict(list)
user_facts = defaultdict(list)
memory_lock = RLock()
facts_lock = RLock()

def load_memory():
    global user_contexts, user_facts
    user_contexts.update(load_json(MEMORY_FILE, {}))
    user_facts.update(load_json(FACTS_FILE, {}))
    print(f"🧠 Memory loaded ({len(user_contexts)} users, {len(user_facts)} profiles)")

def save_memory():
    with memory_lock:
        save_json(MEMORY_FILE, dict(user_contexts))
    with facts_lock:
        save_json(FACTS_FILE, dict(user_facts))

class ContextManager:
    """Handles structured memory, history, and long-term user facts."""
    def __init__(self, user_id):
        self.user_id = user_id
        data = user_contexts.get(user_id, {})
        # Data might be a dict with 'history' and 'facts', or just a list (migration)
        if isinstance(data, dict):
            self.history = data.get("history", [])
            # Facts might come from user_facts.json (newer) or the dict (migration)
            self.facts = user_facts.get(user_id, data.get("facts", []))
        else:
            self.history = data
            self.facts = user_facts.get(user_id, [])

    def add_turn(self, user_msg, bot_reply):
        turn = {"role": "user", "content": user_msg, "timestamp": datetime.datetime.now().isoformat()}
        resp = {"role": "assistant", "content": bot_reply, "timestamp": datetime.datetime.now().isoformat()}
        self.history.append(turn)
        self.history.append(resp)
        
        if len(self.history) > MAX_MEMORY * 2:
            self.history = self.history[-(MAX_MEMORY * 2):]
        
        user_contexts[self.user_id] = {"history": self.history, "facts": self.facts}
        user_facts[self.user_id] = self.facts
        save_memory()
        
        # Trigger fact extraction in background
        Thread(target=self.extract_and_add_facts, args=(user_msg, bot_reply), daemon=True).start()

    def add_fact(self, fact):
        if fact and fact.lower() != "none" and fact not in self.facts:
            self.facts.append(fact)
            user_facts[self.user_id] = self.facts
            save_memory()

    def extract_and_add_facts(self, user_msg, bot_reply):
        try:
            current_facts_str = "; ".join(self.facts) if self.facts else "None"
            prompt = (
                f"{FACT_PROMPT.format(current_facts=current_facts_str)}\n"
                f"--- INTERACTION ---\n"
                f"User: {user_msg}\n"
                f"HomeHub: {bot_reply}"
            )
            payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
            r = requests.post(OLLAMA_URL, json=payload, timeout=30)
            if r.status_code == 200:
                result = r.json().get("response", "NONE").strip()
                if result.lower() != "none":
                    # For simplicity in this logic, we assume the LLM returns the *updated list* 
                    # if the prompt instructions were followed, but to be safe and avoid 
                    # completely overwriting with a partial list, we process it as a set.
                    new_facts = [f.strip() for f in result.split(";") if f.strip()]
                    self.facts = new_facts
                    user_facts[self.user_id] = self.facts
                    save_memory()
        except Exception:
            pass

    def get_prompt_context(self):
        if not self.history:
            return "No previous conversation history."
        formatted = []
        for msg in self.history:
            label = "User" if msg["role"] == "user" else "HomeHub"
            formatted.append(f"{label}: {msg['content']}")
        return "\n".join(formatted)

    def get_facts_summary(self):
        if not self.facts:
            return "No specific details known yet."
        return "- " + "\n- ".join(self.facts)

    def clear(self):
        self.history = []
        self.facts = []
        user_contexts[self.user_id] = []
        user_facts[self.user_id] = []
        save_memory()
