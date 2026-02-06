import json
import datetime
import requests
from config import MODEL_NAME, OLLAMA_URL, INTENT_PROMPT

# Prompt now loaded from config.py

def extract_intent(text, history=""):
    """Single call to determine what the user wants."""
    try:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt = INTENT_PROMPT.format(now=now, text=text, history=history)
        payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
        
        r = requests.post(OLLAMA_URL, json=payload, timeout=30)
        if r.status_code == 200:
            result = r.json().get("response", "").strip()
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
            return data
    except Exception as e:
        print(f"⚠️ Intent extraction error: {e}")
    return {"intent": "chat"}
