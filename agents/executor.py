"""
agents/executor.py â€” Agent 3: Recovery Executor
Executes the recovery plan action by action, logging everything.
"""
import logging

logger = logging.getLogger(__name__)

try:
    from tools.razorpay_tools import (
        retry_payment, send_payment_link, resend_mandate_link,
    )
    from tools.comms_tools import send_sms, send_whatsapp, make_voice_call
    from tools.audit_tools import log_decision, log_action
except ImportError:
    from recoveriq.tools.razorpay_tools import (
        retry_payment, send_payment_link, resend_mandate_link,
    )
    from recoveriq.tools.comms_tools import send_sms, send_whatsapp, make_voice_call
    from recoveriq.tools.audit_tools import log_decision, log_action


_ACTION_DISPATCH = {
    "retry_payment":    lambda p: retry_payment(
                            p.get("payment_id", "pay_unk"),
                            p.get("amount", 0),
                            p.get("method", "upi"),
                        ),
    "send_sms":         lambda p: send_sms(p.get("customer_phone", ""), p.get("template", "payment_failed")),
    "send_whatsapp":    lambda p: send_whatsapp(p.get("customer_phone", ""), p.get("template", "payment_failed")),
    "make_voice_call":  lambda p: make_voice_call(
                            p.get("customer_phone", ""),
                            p.get("customer_name", "Customer"),
                        ),
    "send_payment_link":lambda p: send_payment_link(
                            p.get("customer_phone", ""),
                            p.get("customer_email", ""),
                            p.get("amount", 0),
                            p.get("description", "Pay now"),
                        ),
    "resend_mandate":   lambda p: resend_mandate_link(
                            p.get("customer_phone", ""),
                            p.get("customer_email", ""),
                        ),
    "schedule_retry":   lambda p: {"status": "scheduled", "params": p},
    "escalate":         lambda p: {"status": "escalated", "params": p},
}


class ExecutorAgent:
    """Agent 3 â€” executes the recovery action plan."""

    def run(self, plan: dict, event: dict, run_id: str) -> dict:
        actions = sorted(plan.get("actions", []), key=lambda a: a.get("priority", 99))
        executed = []
        recovered = False
        amount_recovered = 0.0

        log_decision(
            run_id,
            "ExecutorAgent",
            f"Plan for {event.get('id')} â€” {len(actions)} actions",
            plan.get("failure_category", "unknown"),
            plan.get("reasoning", ""),
        )

        for action in actions:
            atype = action.get("action_type", "unknown")
            params = action.get("params", {})

            fn = _ACTION_DISPATCH.get(atype)
            if not fn:
                logger.warning("Unknown action type: %s", atype)
                continue

            try:
                result = fn(params)
            except Exception as exc:
                result = {"success": False, "error": str(exc)}

            success = (
                result.get("status") in ("captured", "scheduled", "escalated")
                or result.get("success") is True
            )

            if success and atype == "retry_payment" and result.get("status") == "captured":
                recovered = True
                amount_recovered = event.get("amount", 0) / 100.0  # paise -> rupees

            log_action(run_id, atype, params, result)
            executed.append({"action_type": atype, "result": result, "success": success})

            logger.info(
                "[Executor] %-20s | %s | %s",
                atype, event.get("id"), "âœ“" if success else "âœ—",
            )

            # Stop retrying if payment is recovered
            if recovered:
                break

        # Determine overall outcome
        if recovered:
            outcome = "RECOVERED"
        elif any(a["action_type"] == "escalate" and a["success"] for a in executed):
            outcome = "ESCALATED"
        elif any(a["success"] for a in executed):
            outcome = "PENDING"
        else:
            outcome = "FAILED"

        return {
            "outcome": outcome,
            "actions_executed": executed,
            "amount_recovered": amount_recovered,
            "recovery_method": next(
                (a["action_type"] for a in executed if a.get("success")), "none"
            ),
        }
