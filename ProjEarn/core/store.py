from threading import Lock
from utils.persistence import load_json, save_json
from config import REMINDERS_FILE, EVENTS_FILE, HABITS_FILE

class DataStore:
    def __init__(self):
        self._reminders = []
        self._events = []
        self._habits = []
        
        # Unified lock for simplicity, or granular if needed.
        # For a single-writer pattern within one process, one lock is safest.
        self._lock = Lock()
        
        self.load_all()

    def load_all(self):
        """Loads all data from disk."""
        with self._lock:
            self._reminders = load_json(REMINDERS_FILE, [])
            self._events = load_json(EVENTS_FILE, [])
            self._habits = load_json(HABITS_FILE, [])
            # Note: We are ignoring the 'cleanup' logic for now to keep store pure.
            # Cleanup should be a business logic operation, not a storage load side-effect.
            print(f"📦 DataStore Loaded: {len(self._reminders)} reminders, {len(self._events)} events, {len(self._habits)} habits")

    # --- Generic Accessors (Reader) ---
    # Return copies to prevent callers from mutating internal state without going through writers
    
    @property
    def reminders(self):
        with self._lock:
            return list(self._reminders) 

    @property
    def events(self):
        with self._lock:
            return list(self._events)

    @property
    def habits(self):
        with self._lock:
            return list(self._habits)

    # --- Atomic Actions (Writer) ---
    # All logic that mutates state MUST go through these methods.
    # The Store controls the persistence timing.

    def add_reminder(self, reminder):
        with self._lock:
            self._reminders.append(reminder)
            save_json(REMINDERS_FILE, self._reminders)
            return reminder

    def update_reminders(self, updated_list):
        """Bulk update (e.g. after marking notifications sent)."""
        with self._lock:
            self._reminders = updated_list
            save_json(REMINDERS_FILE, self._reminders)

    def add_event(self, event):
        with self._lock:
            self._events.append(event)
            save_json(EVENTS_FILE, self._events)
            return event
    
    def update_events(self, updated_list):
        with self._lock:
            self._events = updated_list
            save_json(EVENTS_FILE, self._events)

    def add_habit_entry(self, habit_entry, is_new=False):
        """Adds or updates a habit."""
        with self._lock:
            if is_new:
                self._habits.append(habit_entry)
            else:
                # Find and replace logic? Or caller passes the modified list?
                # Single-writer implies the store assumes valid state input.
                # Ideally, we find the entry by ID and update it.
                # Since we don't have IDs yet, we'll swap the object in place
                # BUT since habit_entry is a ref, if it came from self._habits, it might be mutated already?
                # Safer: caller does the mutation logic, then gives us the full state to save?
                # OR: we act like a DB and take an ID and fields to update.
                
                # For now, let's assume the caller modified the object in the list copy 
                # passing the whole list back is safest for consistency.
                pass 
                # WAIT: The fragility comes from callers mutating objects.
                # Let's trust the caller to pass a VALID modified store-state for bulk updates,
                # or a single item for add. 
            pass
    
    # Let's simplify: The Store *holds* the authoritative list.
    # Operations which mutate specific items (like "mark notified") need a way to do so safely.
    
    def update_habits(self, updated_list):
        with self._lock:
            self._habits = updated_list
            save_json(HABITS_FILE, self._habits)

# Global singleton instance
store = DataStore()
