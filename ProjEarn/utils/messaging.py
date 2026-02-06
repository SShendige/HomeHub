from twilio.rest import Client
from config import ACCOUNT_SID, AUTH_TOKEN, TWILIO_NUMBER, ENABLE_TWILIO

client = None
if ENABLE_TWILIO and ACCOUNT_SID and AUTH_TOKEN:
    client = Client(ACCOUNT_SID, AUTH_TOKEN)

def ensure_whatsapp_addr(num: str) -> str:
    return num if num.startswith("whatsapp:") else f"whatsapp:{num}"

def send_whatsapp(to_number: str, body: str):
    """Send WhatsApp message or print to terminal based on config."""
    if not ENABLE_TWILIO:
        print(f"\n📱 [TERMINAL NOTIFICATION to {to_number}]:\n{body}\n")
        return

    if client:
        try:
            from_addr = ensure_whatsapp_addr(TWILIO_NUMBER)
            to_addr = ensure_whatsapp_addr(to_number)
            msg = client.messages.create(from_=from_addr, to=to_addr, body=body)
            print(f"✅ Message sent via Twilio! SID: {msg.sid}")
        except Exception as e:
            print(f"❌ Twilio send failed: {e}")
            print(f"Fallback terminal output:\n{body}")
    else:
        print(f"⚠️ Twilio disabled or not configured. Content: {body}")
