"""
tools/comms_tools.py — Mocked Twilio comms (SMS, WhatsApp, Voice, Email).
Set TWILIO_MOCK_MODE = False in config.py to send real messages.
"""
import logging, random, time
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from config import TWILIO_MOCK_MODE
except ImportError:
    TWILIO_MOCK_MODE = True


def _delay():
    time.sleep(0.03 + random.random() * 0.05)

def _ts():
    return datetime.now().isoformat()

def _ok(prob=0.95):
    return random.random() < prob


def send_sms(phone, message):
    """Send an SMS via Twilio (mocked)."""
    _delay()
    success = _ok()
    logger.info("[Comms] SMS -> %s | %s | %s", phone, message[:50], "sent" if success else "failed")
    return {"success": success, "channel": "sms", "to": phone, "timestamp": _ts()}


def send_whatsapp(phone, message):
    """Send a WhatsApp message via Twilio (mocked)."""
    _delay()
    success = _ok()
    logger.info("[Comms] WhatsApp -> %s | %s | %s", phone, message[:50], "sent" if success else "failed")
    return {"success": success, "channel": "whatsapp", "to": phone, "timestamp": _ts()}


def make_voice_call(phone, customer_name, script_hinglish=None):
    """Make a Hinglish IVR voice call (mocked)."""
    _delay()
    if not script_hinglish:
        script_hinglish = (
            f"Namaste {customer_name}! Aapka payment fail ho gaya hai. "
            "Kya aap abhi retry karna chahenge? Haan ke liye 1 dabayein, "
            "baad mein karne ke liye 2 dabayein."
        )
    success = _ok(0.80)
    logger.info("[Comms] Voice -> %s | Hinglish IVR | %s", phone, "connected" if success else "no-answer")
    return {
        "success": success,
        "channel": "voice",
        "to": phone,
        "script": script_hinglish,
        "timestamp": _ts(),
        "user_response": "pressed_1" if success else "no_response",
    }


def send_email(email, subject, body):
    """Send an email (mocked)."""
    _delay()
    success = _ok(0.98)
    logger.info("[Comms] Email -> %s | %s", email, subject)
    return {"success": success, "channel": "email", "to": email, "subject": subject, "timestamp": _ts()}
