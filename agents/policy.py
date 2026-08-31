"""
agents/policy.py

RecoverIQ bounded recovery policy engine.

The policy engine decides:
1. How valuable a failed payment is.
2. How recoverable the failure type is.
3. Whether the case should be recovered automatically.
4. Whether the case should be escalated or stopped.

This is intentionally deterministic and explainable.
"""

from dataclasses import dataclass


# ============================================================================
# RECOVERABILITY BY FAILURE TYPE
# ============================================================================

RECOVERABILITY = {
    "NETWORK_ERROR": 0.90,
    "BANK_TIMEOUT": 0.85,
    "INSUFFICIENT_FUNDS": 0.65,
    "CARD_EXPIRED": 0.75,
    "MANDATE_FAILED": 0.60,
    "CHECKOUT_ABANDONED": 0.70,
}


# ============================================================================
# POLICY LIMITS
# ============================================================================

MAX_AUTOMATIC_AMOUNT = 10000.0
MAX_RETRIES = 3


@dataclass
class PolicyDecision:
    """
    Result of the policy evaluation.
    """

    priority_score: float
    priority: str
    recoverability: float
    allowed: bool
    action: str
    reason: str


# ============================================================================
# PRIORITY SCORE
# ============================================================================

def calculate_priority_score(event, diagnosis=None):
    """
    Calculate an explainable 0–100 priority score.

    Factors:
    - payment amount
    - failure recoverability
    - retry history
    """

    amount = float(event.get("amount", 0)) / 100.0

    failure_reason = str(
        event.get("failure_reason", "")
    ).upper()

    retries = int(
        event.get("retry_count", 0) or 0
    )

    # ------------------------------------------------------------
    # Recoverability
    # ------------------------------------------------------------

    recoverability = RECOVERABILITY.get(
        failure_reason,
        0.50,
    )

    # ------------------------------------------------------------
    # Amount score
    # ------------------------------------------------------------

    if amount >= 10000:
        amount_score = 100
    elif amount >= 5000:
        amount_score = 85
    elif amount >= 2000:
        amount_score = 65
    elif amount >= 1000:
        amount_score = 50
    else:
        amount_score = 30

    # ------------------------------------------------------------
    # Retry score
    # ------------------------------------------------------------

    retry_score = max(
        0,
        100 - (retries * 30),
    )

    # ------------------------------------------------------------
    # Final score
    # ------------------------------------------------------------

    score = (
        amount_score * 0.40
        + recoverability * 100 * 0.40
        + retry_score * 0.20
    )

    score = round(
        min(100, max(0, score)),
        1,
    )

    # ------------------------------------------------------------
    # Priority level
    # ------------------------------------------------------------

    if score >= 70:
        priority = "HIGH"

    elif score >= 45:
        priority = "MEDIUM"

    else:
        priority = "LOW"

    return score, priority, recoverability


# ============================================================================
# POLICY CHECK
# ============================================================================

def evaluate_policy(event, diagnosis=None):
    """
    Evaluate whether recovery action is allowed.

    This is the safety boundary around the agent.
    """

    amount = float(
        event.get("amount", 0)
    ) / 100.0

    failure_reason = str(
        event.get("failure_reason", "")
    ).upper()

    retries = int(
        event.get("retry_count", 0) or 0
    )

    score, priority, recoverability = (
        calculate_priority_score(
            event,
            diagnosis,
        )
    )

    # ================================================================
    # STOP RULE 1 — Too many retries
    # ================================================================

    if retries >= MAX_RETRIES:

        return PolicyDecision(
            priority_score=score,
            priority=priority,
            recoverability=recoverability,
            allowed=False,
            action="ESCALATE",
            reason=(
                f"Maximum retry limit reached "
                f"({MAX_RETRIES}). No automatic retry allowed."
            ),
        )

    # ================================================================
    # STOP RULE 2 — Very high-value payment
    # ================================================================

    if amount > MAX_AUTOMATIC_AMOUNT:

        return PolicyDecision(
            priority_score=score,
            priority="HIGH",
            recoverability=recoverability,
            allowed=False,
            action="ESCALATE",
            reason=(
                f"Payment value ₹{amount:,.2f} exceeds "
                f"the automatic recovery limit of "
                f"₹{MAX_AUTOMATIC_AMOUNT:,.2f}."
            ),
        )

    # ================================================================
    # STOP RULE 3 — Unknown failure
    # ================================================================

    if failure_reason not in RECOVERABILITY:

        return PolicyDecision(
            priority_score=score,
            priority=priority,
            recoverability=recoverability,
            allowed=False,
            action="ESCALATE",
            reason=(
                "Failure type is unknown. "
                "Automatic recovery is blocked."
            ),
        )

    # ================================================================
    # ALLOW
    # ================================================================

    if priority == "HIGH":

        action = "PRIORITY_RECOVERY"

    elif priority == "MEDIUM":

        action = "STANDARD_RECOVERY"

    else:

        action = "LOW_PRIORITY_RECOVERY"

    return PolicyDecision(
        priority_score=score,
        priority=priority,
        recoverability=recoverability,
        allowed=True,
        action=action,
        reason=(
            f"Recovery allowed. "
            f"Failure type {failure_reason} has an estimated "
            f"recoverability of {recoverability * 100:.0f}%. "
            f"Priority score is {score}/100."
        ),
    )