"""
config.py — Central configuration for RecoverIQ
Replace placeholder values with your real API keys.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM ──────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_MODEL      = "gemini-3.6-flash"

# ── Razorpay ──────────────────────────────────────────────────────────────────
RAZORPAY_KEY_ID     = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_MOCK_MODE  = False

# ── Twilio (comms) ─────────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE       = os.getenv("TWILIO_PHONE", "+17372508034")
TWILIO_MOCK_MODE   = True

# ── Stopping Rules ────────────────────────────────────────────────────────────
MAX_RETRY_ATTEMPTS   = 3
NO_CONTACT_HOURS     = (22, 8)
MAX_CONTACT_PER_DAY  = 2
ESCALATION_THRESHOLD = 3

# ── Recovery Timing ───────────────────────────────────────────────────────────
SALARY_CREDIT_DAYS   = [1, 28, 29, 30, 31]
IMMEDIATE_RETRY_CODES = ["BAD_REQUEST_ERROR", "GATEWAY_ERROR", "NETWORK_ERROR"]

# ── Audit DB ──────────────────────────────────────────────────────────────────
AUDIT_DB_PATH = "recoveriq_audit.db"

# ── Dashboard ─────────────────────────────────────────────────────────────────
DASHBOARD_TITLE = "RecoverIQ — AI Revenue Recovery Dashboard"
