"""Policy evaluation engine for approval workflow decisions.

Evaluates whether a requested action should be:
  - auto_approve   → execute immediately, no human needed
  - approval_required → create pending approval, wait for agent decision
  - denied         → action is not allowed under current policy

Rules are applied from hardcoded defaults (defaults.py).  A future iteration
can override individual thresholds from the policies DB table.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal, Optional

from app.policy.defaults import (
    CANCEL_APPROVAL_STATUSES,
    CANCEL_AUTO_STATUSES,
    CANCEL_DENIED_STATUSES,
    POLICY_VERSION,
    REFUND_AUTO_THRESHOLD,
    RETURN_WINDOW_DAYS,
)

Outcome = Literal["auto_approve", "approval_required", "denied"]


@dataclass
class PolicyContext:
    """All data the policy engine may need to make a decision."""

    action: str  # issue_refund | cancel_order | email_change | address_change
    amount: Optional[Decimal] = None
    currency: str = "USD"
    order_status: Optional[str] = None
    customer_segment: Optional[str] = None  # standard | premium | enterprise
    order_age_days: Optional[int] = None
    product_categories: list[str] = field(default_factory=list)


@dataclass
class PolicyDecision:
    """Result of a policy evaluation."""

    outcome: Outcome
    policy_id: str          # logical rule that fired
    policy_version: str = POLICY_VERSION
    reason: str = ""        # human-readable explanation
    eligibility_basis: str = ""  # brief structured basis (for audit)


class PolicyEngine:
    """Stateless policy evaluator.  Instantiate once, reuse across requests."""

    # ── Public API ────────────────────────────────────────────────────────────

    def evaluate(self, ctx: PolicyContext) -> PolicyDecision:
        """Return a PolicyDecision for the given context."""
        handler = {
            "issue_refund":   self._eval_refund,
            "cancel_order":   self._eval_cancellation,
            "email_change":   self._eval_account_change,
            "address_change": self._eval_account_change,
        }.get(ctx.action)

        if handler is None:
            return PolicyDecision(
                outcome="approval_required",
                policy_id="unknown_action",
                reason=f"Action '{ctx.action}' has no policy rule; routing to human agent.",
            )
        return handler(ctx)

    # ── Refund ────────────────────────────────────────────────────────────────

    def _eval_refund(self, ctx: PolicyContext) -> PolicyDecision:
        # 1. Return-window check
        if ctx.order_age_days is not None and ctx.order_age_days > RETURN_WINDOW_DAYS:
            return PolicyDecision(
                outcome="denied",
                policy_id="return_window",
                reason=(
                    f"Order is {ctx.order_age_days} days old; "
                    f"return window is {RETURN_WINDOW_DAYS} days."
                ),
                eligibility_basis=f"order_age={ctx.order_age_days}d",
            )

        # 2. Amount threshold check
        threshold = REFUND_AUTO_THRESHOLD.get(
            ctx.customer_segment or "default",
            REFUND_AUTO_THRESHOLD["default"],
        )
        amount = ctx.amount or Decimal("0.00")

        if amount <= threshold:
            return PolicyDecision(
                outcome="auto_approve",
                policy_id="refund_threshold",
                reason=(
                    f"Refund of {ctx.currency} {amount} is within "
                    f"auto-approval threshold ({ctx.currency} {threshold}) "
                    f"for {ctx.customer_segment or 'standard'} segment."
                ),
                eligibility_basis=f"amount={amount} threshold={threshold}",
            )

        return PolicyDecision(
            outcome="approval_required",
            policy_id="refund_threshold",
            reason=(
                f"Refund of {ctx.currency} {amount} exceeds "
                f"auto-approval threshold ({ctx.currency} {threshold}); "
                "requires agent approval."
            ),
            eligibility_basis=f"amount={amount} threshold={threshold}",
        )

    # ── Cancellation ──────────────────────────────────────────────────────────

    def _eval_cancellation(self, ctx: PolicyContext) -> PolicyDecision:
        status = ctx.order_status or ""

        if status in CANCEL_AUTO_STATUSES:
            return PolicyDecision(
                outcome="auto_approve",
                policy_id="cancel_order_status",
                reason=f"Order status '{status}' allows automatic cancellation.",
                eligibility_basis=f"order_status={status}",
            )

        if status in CANCEL_APPROVAL_STATUSES:
            return PolicyDecision(
                outcome="approval_required",
                policy_id="cancel_order_status",
                reason=(
                    f"Order is already '{status}'; "
                    "cancellation requires agent approval."
                ),
                eligibility_basis=f"order_status={status}",
            )

        if status in CANCEL_DENIED_STATUSES:
            return PolicyDecision(
                outcome="denied",
                policy_id="cancel_order_status",
                reason=f"Order status '{status}' does not allow cancellation.",
                eligibility_basis=f"order_status={status}",
            )

        return PolicyDecision(
            outcome="approval_required",
            policy_id="cancel_order_status",
            reason=f"Unknown order status '{status}'; routing to human agent.",
            eligibility_basis=f"order_status={status}",
        )

    # ── Account changes ───────────────────────────────────────────────────────

    def _eval_account_change(self, ctx: PolicyContext) -> PolicyDecision:
        return PolicyDecision(
            outcome="approval_required",
            policy_id="account_change_security",
            reason=(
                f"Action '{ctx.action}' modifies sensitive account data "
                "and always requires agent verification."
            ),
            eligibility_basis=f"action={ctx.action}",
        )
