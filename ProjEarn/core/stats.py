import json
import traceback
from threading import RLock
from config import STATS_FILE
from utils.persistence import load_json

stats_lock = RLock()

def load_stats():
    return load_json(STATS_FILE, {
        "total_messages": 0,
        "unique_users": [],
        "mood_counts": {"positive": 0, "neutral": 0, "negative": 0}
    })

def save_stats(stats):
    """Safely write conversation stats to JSON file."""
    try:
        with stats_lock:
            with open(STATS_FILE, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("❌ [save_stats] Error saving stats:", e)
        traceback.print_exc()

def update_stats(user_number, mood):
    print("📊 Updating stats...")
    try:
        stats = load_stats()
        stats["total_messages"] = stats.get("total_messages", 0) + 1
        uniq = set(stats.get("unique_users", []))
        uniq.add(user_number)
        stats["unique_users"] = list(uniq)
        mood_counts = stats.get("mood_counts", {"positive": 0, "neutral": 0, "negative": 0})
        mood_counts[mood] = mood_counts.get(mood, 0) + 1
        stats["mood_counts"] = mood_counts
        save_stats(stats)
        print(f"✅ Stats updated. Total msgs: {stats['total_messages']}")
    except Exception as e:
        print("❌ Error in update_stats():", e)
        traceback.print_exc()
