"""
tools/razorpay_tools.py — Mocked Razorpay API wrappers.
Set RAZORPAY_MOCK_MODE = False in config.py to hit real test APIs.
"""
import random, time, uuid, logging
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from config import RAZORPAY_MOCK_MODE
except ImportError:
    RAZORPAY_MOCK_MODE = True


def _delay():
    time.sleep(0.05 + random.random() * 0.08)

def _new_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def _ok(prob=0.68):
    return random.random() < prob


def retry_payment(payment_id, amount, method="upi"):
    """Retry a failed payment via an alternate method."""
    _delay()
    success = _ok(0.65)
    logger.info("[Razorpay] retry_payment %s via %s -> %s", payment_id, method, "OK" if success else "FAIL")
    if success:
        return {"status": "captured", "new_payment_id": _new_id("pay"), "method": method}
    return {"status": "failed", "error": "payment_failed", "method": method}


def fetch_payment(payment_id):
    """Fetch payment details (mock)."""
    _delay()
    return {
        "id": payment_id, "status": "failed",
        "amount": random.choice([49900, 99900, 199900]),
        "method": random.choice(["card", "upi", "netbanking"]),
        "created_at": datetime.now().isoformat(),
    }


def send_payment_link(customer_phone, customer_email, amount, description=""):
    """Create and push a Razorpay Payment Link."""
    _delay()
    success = _ok(0.90)
    link_id = _new_id("plink")
    short_url = "https://rzp.io/l/" + link_id[:8]
    logger.info("[Razorpay] payment_link %s -> %s", link_id, short_url)
    return {"success": success, "link_id": link_id, "short_url": short_url, "amount": amount}


def fetch_mandate_status(mandate_id):
    """Fetch NACH/eMandate status (mock)."""
    _delay()
    return {"mandate_id": mandate_id, "status": "rejected", "bank": "HDFC"}


def resend_mandate_link(customer_phone, customer_email):
    """Re-send eMandate authorisation link."""
    _delay()
    success = _ok(0.75)
    mandate_url = "https://rzp.io/m/" + uuid.uuid4().hex[:8]
    logger.info("[Razorpay] resend_mandate to %s -> %s", customer_phone, "OK" if success else "FAIL")
    return {"success": success, "mandate_link": mandate_url}


def fetch_invoice(invoice_id):
    """Fetch invoice details (mock)."""
    _delay()
    return {"id": invoice_id, "status": "overdue", "amount_due": 99900}


def send_invoice_reminder(invoice_id, customer_phone):
    """Send an invoice reminder via Razorpay (mock)."""
    _delay()
    success = _ok(0.80)
    logger.info("[Razorpay] invoice_reminder %s to %s", invoice_id, customer_phone)
    return {"success": success, "invoice_id": invoice_id}
