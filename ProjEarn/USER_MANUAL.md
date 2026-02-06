# HomeHub System User Manual

Welcome to **HomeHub**, your intelligent, warm, and emotionally aware home companion. This document provides a comprehensive guide on how to set up, use, and monitor the HomeHub system.

---

## 1. Introduction
**HomeHub** is a Flask-based AI assistant designed to interact with users via WhatsApp. It uses a local large language model (LLM) powered by **Ollama** to provide human-like, supportive, and culturally relevant conversations. It features persistent memory, sentiment analysis, and a monitoring dashboard.

---

## 2. Key Features
- 🧠 **Persistent Memory**: Remembers the last 5 sets of interactions with each unique user.
- 🎭 **Sentiment Analysis**: Detects user mood (Positive, Neutral, Negative) and adjusts its tone accordingly.
- 💬 **WhatsApp Integration**: Communicates directly through Twilio's WhatsApp API.
- 🛠️ **Slash Commands**: Quick commands for help, summaries, and memory management.
- 📊 **Monitoring Dashboard**: Real-time view of message statistics and recent logs.
- 📈 **Metrics Interface**: Prometheus-compatible endpoint for system health and usage tracking.

---

## 3. Prerequisites
Before setting up HomeHub, ensure you have the following installed and configured:
- **Python 3.8+**
- **Ollama**: Installed and running locally.
  - Download from: [ollama.com](https://ollama.com)
  - Model required: `mistral` (Run `ollama run mistral` to download).
- **Twilio Account**:
  - Twilio Account SID and Auth Token.
  - A registered Twilio WhatsApp Number (or Sandbox).
- **Internet Connection**: Required for Twilio API calls.

---

## 4. Project Structure (Clean Architecture)
```text
ProjEarn/
├── app.py              # Main entry point (Flask Routes)
├── config.py           # Centralized configuration & prompts
├── core/
│   ├── memory.py         # ContextManager & Fact Management
│   ├── llm.py            # Ollama API logic
│   ├── sentiment.py      # Mood analysis
│   └── stats.py          # Metrics & statistics
├── utils/
│   ├── messaging.py      # Twilio WhatsApp integration
│   ├── persistence.py    # JSON read/write helpers
│   └── logger.py         # Interaction logging
└── data/               # Persistent storage (JSON files, logs)
```

---

## 5. Installation & Setup

### Step 1: Clone or Copy the Repository
Ensure all files (`app.py`, `.env`, etc.) are in your project directory.

### Step 2: Install Dependencies
Run the following command to install required libraries:
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Create or edit the `.env` file in the root directory with your credentials:
```env
TWILIO_ACCOUNT_SID=your_sid_here
TWILIO_AUTH_TOKEN=your_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890
PORT=5000 (optional, defaults to 5000)
```

---

## 5. Usage

### Starting the Server
Run the application:
```bash
python app.py
```
The server will start on `http://0.0.0.0:5000`.

### Interacting via WhatsApp
Once your Twilio webhook is configured to point to `your-domain.com/whatsapp`, you can simply message the configured number.

### Chat Commands
You can send these commands directly in the WhatsApp chat:
| Command | Description |
| :--- | :--- |
| `help` | Displays the help menu. |
| `summary` | Shows a recap of the last few messages in the current session. |
| `forget` | Clears your conversation history from HomeHub's memory. |

### Testing without WhatsApp
You can simulate a user message using your browser or `curl`:
`http://localhost:5000/simulate?text=Hello HomeHub&from=my-id`

---

## 6. Monitoring & Management

### Dashboard
View system stats and recent logs visually:
- **URL**: `http://localhost:5000/dashboard`
- **Shows**: Total messages, unique users, mood distribution, and the last 50 log entries.

### Metrics
For technical monitoring or integration with tools like Prometheus:
- **URL**: `http://localhost:5000/metrics`

### Health Check
Verify the system status:
- **URL**: `http://localhost:5000/health`

---

## 7. Data Persistence & Context Management
HomeHub maintains state using a structured `data/` directory:
- `data/reminders.json`: Stores scheduled active reminders.
- `data/events.json`: Stores recorded events and meetings.
- `data/habits.json`: Stores tracked habits and streaks.
- `data/memory.json`: Stores user context, conversation history, and timestamps.

### Terminal Mode (Binary Toggle)
In `config.py`, setting `ENABLE_TWILIO = False` disconnects the Twilio API. All notifications (replies, reminders, and events) will be printed directly to the system terminal instead of being sent to WhatsApp.

### Reminders, Events & Habits
HomeHub can now manage short-term tasks, long-term schedules, and daily habits.
- **Reminders**: Quick tasks (e.g., "Remind me in 5 mins to check the oven").
- **Events**: Meetings or daily activities (e.g., "I have a meeting tomorrow at 3pm").
- **Habits**: Daily tracking (e.g., "I just finished my morning run" or "Did 30 mins of reading"). 
  - Tracks streaks and total completions.
- **View Lists**: 
  - Reminders: `http://localhost:5000/listreminders?from=dev-user`
  - Events: `http://localhost:5000/listevents?from=dev-user`
  - Habits: `http://localhost:5000/listhabits?from=dev-user`
  - Summary (Facts + History): `http://localhost:5000/forcesummary?from=dev-user`
  - Manual Briefing: `http://localhost:5000/morning?from=dev-user`

---

## 8. Troubleshooting
- **Ollama Connection Error**: Ensure Ollama is running (`ollama serve`) and the `mistral` model is pulled.
- **Twilio Errors**: Verify your SID and Token in `.env`. Check if your WhatsApp Sandbox is active.
- **Port Conflict**: If port 5000 is taken, change the `PORT` variable in `.env`.

---
*Created by HomeHub Development Team*
