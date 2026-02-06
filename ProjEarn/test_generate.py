import requests, json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"
SYS_PROMPT = (
    "You are HomeHub, a warm, funny, empathetic home companion who speaks like a best friend. "
    "Keep replies short and practical. Avoid technical jargon."
)

def generate_reply(user_text):
    payload = {
        "model": MODEL_NAME,
        "prompt": f"{SYS_PROMPT}\nUser: {user_text}\nHomeHub:"
    }
    print("⏳ Sending request to Ollama...")
    r = requests.post(OLLAMA_URL, json=payload, timeout=120)
    print("✅ Ollama response status:", r.status_code)

    reply = ""
    for line in r.text.splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            if "response" in data:
                reply += data["response"]
            if data.get("done", False):
                break
        except json.JSONDecodeError:
            reply += line

    print("\n💬 Final Reply:\n", reply.strip() or "(empty)")

if __name__ == "__main__":
    generate_reply("hi homehub, how are you?")
