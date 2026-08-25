"""
agents/strategist.py â€” Agent 2: Recovery Strategist
Picks the best recovery action sequence, respecting stopping rules.
"""
import json, logging
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from config import (
        MAX_RETRY_ATTEMPTS, NO_CONTACT_HOURS, MAX_CONTACT_PER_DAY,
        SALARY_CREDIT_DAYS, GEMINI_API_KEY, LLM_MODEL,
    )
except ImportError:
    MAX_RETRY_ATTEMPTS = 3
    NO_CONTACT_HOURS = (22, 8)
    MAX_CONTACT_PER_DAY = 2
    SALARY_CREDIT_DAYS = [1, 28, 29, 30, 31]
    GEMINI_API_KEY = ""
    LLM_MODEL = "gemini-1.5-flash"


# ---------------------------------------------------------------------------
# Rule-based strategy table
# ---------------------------------------------------------------------------
_STRATEGY_TABLE = {
    "INSUFFICIENT_FUNDS": [
        {"action_type": "send_whatsapp",   "priority": 1, "timing": "immediate",
         "params": {"template": "insufficient_funds_reminder"}},
        {"action_type": "schedule_retry",  "priority": 2, "timing": "salary_day",
         "params": {"retry_on_days": SALARY_CREDIT_DAYS}},
    ],
    "CARD_EXPIRED": [
        {"action_type": "send_whatsapp",   "priority": 1, "timing": "immediate",
         "params": {"template": "card_expired_update_link"}},
        {"action_type": "send_sms",        "priority": 2, "timing": "immediate",
         "params": {"template": "card_expired_sms"}},
        {"action_type": "send_payment_link","priority": 3, "timing": "immediate",
         "params": {"description": "Update card and pay"}},
    ],
    "BANK_TIMEOUT": [
        {"action_type": "retry_payment",   "priority": 1, "timing": "immediate",
         "params": {"method": "upi"}},
        {"action_type": "retry_payment",   "priority": 2, "timing": "immediate",
         "params": {"method": "netbanking"}},
    ],
    "MANDATE_FAILED": [
        {"action_type": "resend_mandate",  "priority": 1, "timing": "immediate",
         "params": {}},
        {"action_type": "send_whatsapp",   "priority": 2, "timing": "immediate",
         "params": {"template": "mandate_reauth"}},
    ],
    "CHECKOUT_ABANDONED": [
        {"action_type": "send_whatsapp",   "priority": 1, "timing": "immediate",
         "params": {"template": "checkout_recovery"}},
        {"action_type": "make_voice_call", "priority": 2, "timing": "immediate",
         "params": {"language": "hinglish"}},
        {"action_type": "send_payment_link","priority": 3, "timing": "1_hour_later",
         "params": {"description": "Complete your purchase"}},
    ],
    "NETWORK_ERROR": [
        {"action_type": "retry_payment",   "priority": 1, "timing": "immediate",
         "params": {"method": "same"}},
        {"action_type": "retry_payment",   "priority": 2, "timing": "immediate",
         "params": {"method": "upi"}},
    ],
}


def _within_contact_hours() -> bool:
    hour = datetime.now().hour
    start, end = NO_CONTACT_HOURS
    if start > end:
        return not (hour >= start or hour < end)
    return not (start <= hour < end)


def _check_stopping_rules(event: dict) -> tuple[bool, str]:
    if event.get("retry_count", 0) >= MAX_RETRY_ATTEMPTS:
        return False, f"Max retry attempts ({MAX_RETRY_ATTEMPTS}) reached"
    if not _within_contact_hours():
        return False, "Outside contact hours â€” will schedule for morning"
    return True, "OK"


class StrategistAgent:
    """Agent 2 â€” builds the recovery action plan."""

    def run(self, diagnosis: dict, event: dict) -> dict:
        compliant, reason = _check_stopping_rules(event)
        category = diagnosis.get("failure_category", "NETWORK_ERROR")
        actions = _STRATEGY_TABLE.get(category, _STRATEGY_TABLE["NETWORK_ERROR"])

        # Enrich actions with event context
        enriched = []
        for a in actions:
            enriched_action = dict(a)
            enriched_action["params"] = dict(a.get("params", {}))
            enriched_action["params"].update({
                "customer_phone": event.get("customer_phone"),
                "customer_email": event.get("customer_email"),
                "customer_name":  event.get("customer_name"),
                "amount":         event.get("amount"),
                "payment_id":     event.get("id"),
            })
            enriched.append(enriched_action)

        plan = {
            "actions": enriched,
            "max_attempts": MAX_RETRY_ATTEMPTS,
            "escalate_after": 3,
            "reasoning": (
                f"Strategy for {category}: {diagnosis.get('recommended_strategy', '')}. "
                f"Stopping rules: {reason}."
            ),
            "compliant": compliant,
            "failure_category": category,
        }

        if not compliant:
            plan["actions"] = [
                {
                    "action_type": "schedule_retry",
                    "priority": 1,
                    "timing": "next_morning",
                    "params": {"reason": reason, "payment_id": event.get("id")},
                }
            ]

        logger.info("StrategistAgent: %d actions planned for %s", len(plan["actions"]), category)
        return plan
