import os
from dotenv import load_dotenv

load_dotenv()

# API Keys & Auth
ENABLE_TWILIO = False  # Set to True to enable WhatsApp, False for Terminal only
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
PORT = int(os.getenv("PORT", 5000))

# Ollama Settings
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"

# File Paths
DATA_DIR = "data"
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
FACTS_FILE = os.path.join(DATA_DIR, "user_facts.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")
REMINDERS_FILE = os.path.join(DATA_DIR, "reminders.json")
EVENTS_FILE = os.path.join(DATA_DIR, "events.json")
HABITS_FILE = os.path.join(DATA_DIR, "habits.json")
LOG_FILE = os.path.join(DATA_DIR, "conversation_logs.txt")

# Behavior
MAX_MEMORY = 7
DEFAULT_WAKE_TIME = "07:30"
DEFAULT_CITY = "Bengaluru"
SYS_PROMPT = (
    "You are HomeHub, a warm, caring, and emotionally intelligent home companion. "
    "Your primary role is to be a supportive friend who listens and chats with the user. "
    "Keep replies short, human, and focused on emotional connection. "
    "While you can help with tasks, prioritize being a great conversationalist. "
    "NEVER mention internal system logs or technical notes. You live in India."
)

FACT_PROMPT = (
    "You are HomeHub's long-term memory module. Analyze the interaction and the current 'Known Facts' list. "
    "Your goal is to extract personal facts about the user (name, location, preferences, waking up time, family, etc.).\n"
    "Rules:\n"
    "1. If new information contradicts a 'Known Fact', replace the old fact.\n"
    "2. If new info is found, add it (e.g., 'Wake up time: 08:00', 'Location: Mumbai').\n"
    "3. Format exactly as a semicolon-separated list of facts.\n"
    "4. Return 'NONE' if there is absolutely no new or changed information.\n"
    "Current Known Facts: {current_facts}"
)

BRIEFING_PROMPT = (
    "You are HomeHub, giving a warm morning briefing to the user. "
    "Current Date: {date}\n"
    "Weather in {city}: {weather}\n"
    "--- TODAY'S AGENDA ---\n"
    "Events: {events}\n"
    "Reminders: {reminders}\n"
    "--- TASK ---\n"
    "1. Analyze the schedule. Are there back-to-back events? Is it a heavy day?\n"
    "2. If busy, suggest a specific strategic break (e.g. 'You have 3 meetings in a row, maybe take a walk at 2pm?').\n"
    "3. If light, suggest working on a habit or taking time for themselves.\n"
    "4. Write a friendly, warm morning briefing that includes this proactive advice."
)

# --- Task Extraction Prompts ---

INTENT_PROMPT = (
    "Analyze the user input and decide if they are asking for a reminder, recording an event/meeting, "
    "reporting a habit completion, or just chatting/sharing feelings.\n"
    "Current Time: {now} (Year: 2025, Month: 12, Day: 27, Saturday)\n"
    "Conversation History:\n{history}\n"
    "User Input: '{text}'\n\n"
    "Categories:\n"
    "1. 'reminder': FUTURE task with a time (e.g. 'remind me tomorrow', 'need to do X at 5pm').\n"
    "2. 'event': FUTURE formal meeting or professional plan (e.g. 'meeting on Monday', 'dentist visit').\n"
    "3. 'habit': POSITIVE report of completing a routine today (e.g. 'did my workout', 'finished reading').\n"
    "4. 'chat': General conversation, sharing feelings, venting, or past-tense reports that don't need tracking (e.g. 'I missed the gym', 'I feel sad').\n\n"
    "Format exactly as JSON:\n"
    "{{\n"
    "  \"intent\": \"reminder|event|habit|chat\",\n"
    "  \"task_title\": \"(if applicable)\",\n"
    "  \"time\": \"YYYY-MM-DDTHH:MM:SS (if applicable)\",\n"
    "  \"confidence\": 0.0 to 1.0\n"
    "}}"
)

REMINDER_EXTRACT_PROMPT = (
    "Extract only FUTURE tasks/reminders. The user is currently in India.\n"
    "Current Time context: {now} (Year: 2025, Month: 12, Day: 27, Saturday)\n"
    "Task: Extract any FUTURE reminder or event from: '{text}'\n\n"
    "STRICT RULES:\n"
    "1. If the message is about the PAST (e.g., 'i missed', 'I did', 'I finished'), is_reminder must be FALSE.\n"
    "2. If it is about the FUTURE (e.g., 'remind me', 'i need to', 'will do'), calculate the date.\n"
    "3. Date Calculation:\n"
    "   - 'Monday' = 2025-12-29\n"
    "   - 'Tomorrow' = 2025-12-28\n"
    "4. Return EXACTLY this format:\n"
    "{{\"task\": \"task name\", \"time\": \"YYYY-MM-DDTHH:MM:SS\", \"is_reminder\": true}}\n"
    "5. If no FUTURE reminder is found, return exactly: {{\"is_reminder\": false}}"
)

EVENT_EXTRACT_PROMPT = (
    "Extract only FUTURE professional or social events (meetings, plans).\n"
    "Current date/time: {now} (Year: 2025, Month: 12, Day: 27, Saturday)\n"
    "Task: Extract any FUTURE event from: '{text}'\n\n"
    "Rules:\n"
    "1. Only extract if it's a FUTURE meeting or plan. NOT things already done.\n"
    "2. If day is mentioned ('on Monday'), use 2025-12-29.\n"
    "3. Format exactly as JSON:\n"
    "{{\"title\": \"event title\", \"time\": \"YYYY-MM-DDTHH:MM:SS\", \"is_event\": true}}\n"
    "If no future event is intended, return: {{\"is_event\": false}}"
)

HABIT_EXTRACT_PROMPT = (
    "Extract the habit name ONLY if the user is reporting a POSITIVE completion today.\n"
    "User Input: '{text}'\n\n"
    "Rules:\n"
    "- extract only if they did, finished, or are reporting success.\n"
    "- If the user says they 'missed', 'forgot', or 'skipped', this is NOT a completion.\n"
    "- Format exactly as JSON:\n"
    "{{\"habit\": \"habit name\", \"is_completion\": true}}\n"
    "If no completion is reported, return {{\"is_completion\": false}}"
)

# Help Text
HELP_TEXT = (
    "🤖 *HomeHub Commands*\n"
    "/help - Show this help menu\n"
    "/summary - Recap our last few messages & known facts\n"
    "/forget - Clear my memory for this chat\n"
)
