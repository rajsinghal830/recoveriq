"""
agents/detector.py â€” Agent 1: Root Cause Detector
Classifies why a payment failed and produces a structured diagnosis.
Falls back to rule-based logic if the LLM is unavailable.
"""
import json, logging, os, sys

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rule-based fallback classifier (no LLM needed)
# ---------------------------------------------------------------------------
_SEVERITY_MAP = {
    "INSUFFICIENT_FUNDS":  ("MEDIUM", "scheduled"),
    "CARD_EXPIRED":        ("MEDIUM", "scheduled"),
    "BANK_TIMEOUT":        ("LOW",    "immediate"),
    "MANDATE_FAILED":      ("HIGH",   "scheduled"),
    "CHECKOUT_ABANDONED":  ("MEDIUM", "immediate"),
    "NETWORK_ERROR":       ("LOW",    "immediate"),
}

_STRATEGY_MAP = {
    "INSUFFICIENT_FUNDS":  "Retry on salary credit day; send WhatsApp reminder",
    "CARD_EXPIRED":        "Prompt user to update card via payment link",
    "BANK_TIMEOUT":        "Immediately retry with UPI; switch acquirer",
    "MANDATE_FAILED":      "Re-send eMandate authorisation link via WhatsApp",
    "CHECKOUT_ABANDONED":  "Re-engage via WhatsApp + Hinglish voice call",
    "NETWORK_ERROR":       "Instant retry; no user contact needed",
}


def rule_based_classify(event: dict) -> dict:
    reason = event.get("failure_reason", "NETWORK_ERROR").upper()
    severity, window = _SEVERITY_MAP.get(reason, ("MEDIUM", "immediate"))
    return {
        "failure_category": reason,
        "severity": severity,
        "recovery_window": window,
        "reasoning": f"Rule-based: {reason} mapped to {severity} severity",
        "recommended_strategy": _STRATEGY_MAP.get(reason, "Retry payment"),
        "source": "rule_based",
    }


# ---------------------------------------------------------------------------
# LLM-powered classifier
# ---------------------------------------------------------------------------
def _build_prompt(event: dict) -> str:
    return f"""You are a payment failure analyst. Diagnose this failed payment and return ONLY a JSON object.

Payment event:
- ID: {event.get("id")}
- Failure reason: {event.get("failure_reason")}
- Error code: {event.get("error_code")}
- Payment method: {event.get("payment_method")}
- Amount (paise): {event.get("amount")}
- Retry count: {event.get("retry_count", 0)}

Return ONLY this JSON (no markdown):
{{
  "failure_category": "<one of: INSUFFICIENT_FUNDS | CARD_EXPIRED | BANK_TIMEOUT | MANDATE_FAILED | CHECKOUT_ABANDONED | NETWORK_ERROR>",
  "severity": "<HIGH | MEDIUM | LOW>",
  "recovery_window": "<immediate | scheduled | manual>",
  "reasoning": "<1-2 sentence explanation>",
  "recommended_strategy": "<concise action recommendation>"
}}"""


class DetectorAgent:
    """Agent 1 â€” classifies the root cause of a payment failure."""

    def __init__(self):
        self.llm = None
        self._init_llm()

    def _init_llm(self):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from config import GEMINI_API_KEY, LLM_MODEL
            if GEMINI_API_KEY and "YOUR_" not in GEMINI_API_KEY:
                self.llm = ChatGoogleGenerativeAI(
                    model=LLM_MODEL,
                    google_api_key=GEMINI_API_KEY,
                    temperature=0.1,
                    max_retries= 0,
                )
                logger.info("DetectorAgent: Gemini LLM ready")
            else:
                logger.warning("DetectorAgent: No Gemini API key â€” using rule-based fallback")
        except Exception as exc:
            logger.warning("DetectorAgent: LLM init failed (%s) â€” using rule-based fallback", exc)

    def run(self, event: dict) -> dict:
        """Run root-cause detection on a payment failure event."""

        # Use deterministic rules for common failure types.
        # This avoids wasting Gemini calls on obvious cases.
        reason = event.get("failure_reason", "NETWORK_ERROR").upper()

        common_failures = {
            "INSUFFICIENT_FUNDS",
            "CARD_EXPIRED",
            "BANK_TIMEOUT",
            "MANDATE_FAILED",
            "CHECKOUT_ABANDONED",
            "NETWORK_ERROR",
        }

        if reason in common_failures:
            return rule_based_classify(event)

        # Use Gemini only for cases where AI reasoning adds more value.
        if self.llm is None:
            return rule_based_classify(event)

        try:
            prompt = _build_prompt(event)
            response = self.llm.invoke(prompt)
            content = response.content

            if isinstance(content, list):
                raw = "".join(
                    item.get("text", "") if isinstance(item, dict) else str(item)
                    for item in content
                ).strip()
            else:
                raw = str(content).strip()

            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            diagnosis = json.loads(raw)
            diagnosis["source"] = "llm"
            return diagnosis

        except Exception as exc:
            logger.warning(
                "DetectorAgent LLM error (%s) — falling back",
                exc
            )

            result = rule_based_classify(event)
            result["source"] = "rule_based_fallback"
            return result