import os
import datetime
import traceback
import time
import json
from threading import Thread
from flask import Flask, request, jsonify, Response
from twilio.twiml.messaging_response import MessagingResponse

# Project modules
from config import PORT, LOG_FILE, TWILIO_NUMBER, HELP_TEXT
import config
from utils.messaging import send_whatsapp
from utils.persistence import load_json
from core.memory import load_memory, ContextManager, user_contexts
from core.llm import generate_reply
from core.stats import update_stats, load_stats
from core.reminders import start_reminder_scheduler, run_reminders_check
from core.events import start_event_scheduler, run_events_check
from core.store import store
from core.briefing import check_and_send_briefings, generate_morning_briefing

app = Flask(__name__)

# ============================================================
#  Logging Helper
# ============================================================

def log_message(user_number, user_msg, bot_reply):
    with open(config.LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.datetime.now()}] {user_number}\nUser: {user_msg}\nHomeHub: {bot_reply}\n")

# ============================================================
#  Command Handler
# ============================================================

def handle_commands_or_generate(user_text, user_number):
    print(f"⚙️ Handling input: {user_text}")
    txt = user_text.strip().lower()
    
    if txt in ["help", "/help"]:
        return config.HELP_TEXT
    
    if txt in ["summary", "/summary"]:
        ctx_mgr = ContextManager(user_number)
        history = ctx_mgr.get_prompt_context()
        facts = ctx_mgr.get_facts_summary()
        return f"🧠 *Recent Memory for {user_number}*\n\n📋 *Facts Known:*\n{facts}\n\n💬 *History:*\n{history}"
    
    if txt in ["forget", "/forget"]:
        ctx_mgr = ContextManager(user_number)
        ctx_mgr.clear()
        return "🧹 Cleared memory for this chat."

    return generate_reply(user_text, user_number, update_stats_callback=update_stats)

# ============================================================
#  Flask Routes
# ============================================================

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    msg = (request.values.get("Body") or "").strip()
    from_num = (request.values.get("From") or "").strip()

    if not msg or not from_num:
        return "Error: Invalid request", 400

    print(f"📩 From {from_num}: {msg}")
    
    def background_task(text, num):
        try:
            reply = handle_commands_or_generate(text, num)
            send_whatsapp(num, reply)
            log_message(num, text, reply)
        except Exception as e:
            print(f"❌ Background error: {e}")
            send_whatsapp(num, "⚠️ Sorry, something went wrong.")

    Thread(target=background_task, args=(msg, from_num), daemon=True).start()
    return str(MessagingResponse())

@app.route("/simulate")
def simulate():
    user_number = request.args.get("from", "dev-user")
    user_text = request.args.get("text", "").strip()

    if not user_text:
        return jsonify({"error": "Provide ?text= parameter"}), 400

    try:
        reply = handle_commands_or_generate(user_text, user_number)
        log_message(user_number, user_text, reply)
        return jsonify({
            "from": user_number,
            "reply": reply,
            "timestamp": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/listreminders")
def list_reminders():
    """Endpoint to list all active reminders."""
    user_id = request.args.get("from", "dev-user")
    user_id = request.args.get("from", "dev-user")
    user_reminders = [r for r in store.reminders if r["user_id"] == user_id or user_id == "admin"]
    return jsonify({
        "user_id": user_id,
        "count": len(user_reminders),
        "reminders": user_reminders
    })

@app.route("/listevents")
def list_events():
    """Endpoint to list all recorded events."""
    user_id = request.args.get("from", "dev-user")
    user_id = request.args.get("from", "dev-user")
    user_events = [e for e in store.events if e["user_id"] == user_id or user_id == "admin"]
    return jsonify({
        "user_id": user_id,
        "count": len(user_events),
        "events": user_events
    })

@app.route("/listhabits")
def list_habits():
    """Endpoint to list all tracked habits."""
    user_id = request.args.get("from", "dev-user")
    user_id = request.args.get("from", "dev-user")
    user_habits = [h for h in store.habits if h["user_id"] == user_id or user_id == "admin"]
    return jsonify({
        "user_id": user_id,
        "count": len(user_habits),
        "habits": user_habits
    })

@app.route("/forcecheck")
def force_check():
    """Manually trigger due reminders and events check + briefings."""
    r_count = run_reminders_check()
    e_count = run_events_check()
    check_and_send_briefings() # Also check briefings
    return jsonify({
        "status": "success",
        "reminders_triggered": r_count,
        "events_triggered": e_count,
        "briefings_checked": True,
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route("/morning")
def morning_briefing():
    """Manually trigger a morning briefing for a user."""
    user_id = request.args.get("from", "dev-user")
    success = generate_morning_briefing(user_id)
    return jsonify({
        "status": "success" if success else "failed",
        "user_id": user_id,
        "type": "manual_briefing"
    })

@app.route("/forcesummary")
def forcesummary():
    """Manually retrieve memory summary (facts + history) for a user."""
    user_id = request.args.get("from", "dev-user")
    ctx_mgr = ContextManager(user_id)
    history = ctx_mgr.get_prompt_context()
    facts = ctx_mgr.get_facts_summary()
    return jsonify({
        "user_id": user_id,
        "facts": facts,
        "history": history,
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route("/metrics")
def metrics():
    s = load_stats()
    moods = s.get("mood_counts", {})
    lines = [
        f'homehub_total_messages {s.get("total_messages", 0)}',
        f'homehub_unique_users {len(s.get("unique_users", []))}',
        f'homehub_mood_positive {moods.get("positive", 0)}',
        f'homehub_mood_neutral {moods.get("neutral", 0)}',
        f'homehub_mood_negative {moods.get("negative", 0)}'
    ]
    return Response("\n".join(lines), mimetype="text/plain")

@app.route("/dashboard")
def dashboard():
    s = load_stats()
    recent_logs = ""
    if os.path.exists(config.LOG_FILE):
        with open(config.LOG_FILE, "r", encoding="utf-8") as f:
            recent_logs = "\n".join(f.read().splitlines()[-50:])
    
    html = f"""
    <html><head><title>HomeHub Dashboard</title></head>
    <body style="font-family:sans-serif;padding:20px;background:#f4f4f9">
      <h1>📊 HomeHub Dashboard</h1>
      <div style="background:white;padding:15px;border-radius:8px;box-shadow:0 2px 5px rgba(0,0,0,0.1)">
          <p><b>Total Messages:</b> {s.get('total_messages',0)}</p>
          <p><b>Unique Users:</b> {len(s.get('unique_users',[]))}</p>
          <h3>Moods</h3>
          <pre>{json.dumps(moods, indent=2) if (moods:=s.get('mood_counts')) else "{}"}</pre>
      </div>
      <h3>Recent Logs</h3>
      <pre style="background:#222;color:#eee;padding:15px;border-radius:8px;overflow-x:auto">{recent_logs}</pre>
    </body></html>
    """
    return Response(html, mimetype="text/html")

@app.route("/")
def home():
    return "✅ HomeHub is healthy and running!"

# ============================================================
#  Main Runner
# ============================================================

def start_briefing_scheduler():
    def briefing_loop():
        while True:
            try:
                check_and_send_briefings()
            except Exception as e:
                print(f"⚠️ Briefing loop error: {e}")
            time.sleep(60) # Only check every minute
    Thread(target=briefing_loop, daemon=True).start()

if __name__ == "__main__":
    print(f"🚀 Starting HomeHub on port {config.PORT}")
    load_memory()
    print(f"🚀 Starting HomeHub on port {config.PORT}")
    load_memory()
    # DataStore loads automatically on import
    start_reminder_scheduler()
    start_event_scheduler()
    start_briefing_scheduler()
    app.run(host="0.0.0.0", port=config.PORT, debug=True)
