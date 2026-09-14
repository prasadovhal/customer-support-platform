"""Unit tests for the Phase 12 policy engine."""
from __future__ import annotations

from decimal import Decimal


from app.policy.engine import PolicyContext, PolicyDecision, PolicyEngine

engine = PolicyEngine()


# ── Refund policy ─────────────────────────────────────────────────────────────


class TestRefundPolicy:
    def test_small_refund_standard_auto_approved(self):
        ctx = PolicyContext(
            action="issue_refund", amount=Decimal("30.00"), customer_segment="standard"
        )
        d = engine.evaluate(ctx)
        assert d.outcome == "auto_approve"
        assert d.policy_id == "refund_threshold"

    def test_refund_at_threshold_auto_approved(self):
        ctx = PolicyContext(
            action="issue_refund", amount=Decimal("50.00"), customer_segment="standard"
        )
        d = engine.evaluate(ctx)
        assert d.outcome == "auto_approve"

    def test_refund_above_threshold_requires_approval(self):
        ctx = PolicyContext(
            action="issue_refund", amount=Decimal("75.00"), customer_segment="standard"
        )
        d = engine.evaluate(ctx)
        assert d.outcome == "approval_required"

    def test_premium_customer_higher_threshold(self):
        # $80 is above standard ($50) but below premium ($100)
        ctx = PolicyContext(
            action="issue_refund", amount=Decimal("80.00"), customer_segment="premium"
        )
        d = engine.evaluate(ctx)
        assert d.outcome == "auto_approve"

    def test_enterprise_customer_highest_threshold(self):
        ctx = PolicyContext(
            action="issue_refund",
            amount=Decimal("150.00"),
            customer_segment="enterprise",
        )
        d = engine.evaluate(ctx)
        assert d.outcome == "auto_approve"

    def test_enterprise_refund_above_threshold_requires_approval(self):
        ctx = PolicyContext(
            action="issue_refund",
            amount=Decimal("250.00"),
            customer_segment="enterprise",
        )
        d = engine.evaluate(ctx)
        assert d.outcome == "approval_required"

    def test_refund_within_return_window(self):
        ctx = PolicyContext(
            action="issue_refund", amount=Decimal("20.00"), order_age_days=15
        )
        d = engine.evaluate(ctx)
        assert d.outcome == "auto_approve"

    def test_refund_outside_return_window_denied(self):
        ctx = PolicyContext(
            action="issue_refund", amount=Decimal("20.00"), order_age_days=45
        )
        d = engine.evaluate(ctx)
        assert d.outcome == "denied"
        assert d.policy_id == "return_window"
        assert "45" in d.reason

    def test_refund_exactly_at_window_boundary_allowed(self):
        ctx = PolicyContext(
            action="issue_refund", amount=Decimal("20.00"), order_age_days=30
        )
        d = engine.evaluate(ctx)
        # 30 days is exactly the window — should still be allowed (> not >=)
        assert d.outcome != "denied"

    def test_refund_no_amount_defaults_to_zero(self):
        ctx = PolicyContext(
            action="issue_refund", amount=None, customer_segment="standard"
        )
        d = engine.evaluate(ctx)
        assert d.outcome == "auto_approve"

    def test_decision_has_reason(self):
        ctx = PolicyContext(action="issue_refund", amount=Decimal("30.00"))
        d = engine.evaluate(ctx)
        assert len(d.reason) > 0

    def test_decision_has_policy_version(self):
        ctx = PolicyContext(action="issue_refund", amount=Decimal("30.00"))
        d = engine.evaluate(ctx)
        assert d.policy_version != ""


# ── Cancellation policy ───────────────────────────────────────────────────────


class TestCancellationPolicy:
    def test_pending_order_auto_approved(self):
        ctx = PolicyContext(action="cancel_order", order_status="pending")
        d = engine.evaluate(ctx)
        assert d.outcome == "auto_approve"

    def test_processing_order_auto_approved(self):
        ctx = PolicyContext(action="cancel_order", order_status="processing")
        d = engine.evaluate(ctx)
        assert d.outcome == "auto_approve"

    def test_shipped_order_requires_approval(self):
        ctx = PolicyContext(action="cancel_order", order_status="shipped")
        d = engine.evaluate(ctx)
        assert d.outcome == "approval_required"

    def test_delivered_order_denied(self):
        ctx = PolicyContext(action="cancel_order", order_status="delivered")
        d = engine.evaluate(ctx)
        assert d.outcome == "denied"

    def test_already_cancelled_denied(self):
        ctx = PolicyContext(action="cancel_order", order_status="cancelled")
        d = engine.evaluate(ctx)
        assert d.outcome == "denied"

    def test_refunded_order_denied(self):
        ctx = PolicyContext(action="cancel_order", order_status="refunded")
        d = engine.evaluate(ctx)
        assert d.outcome == "denied"

    def test_unknown_status_requires_approval(self):
        ctx = PolicyContext(action="cancel_order", order_status="mystery_status")
        d = engine.evaluate(ctx)
        assert d.outcome == "approval_required"

    def test_no_status_requires_approval(self):
        ctx = PolicyContext(action="cancel_order", order_status=None)
        d = engine.evaluate(ctx)
        assert d.outcome == "approval_required"


# ── Account change policy ─────────────────────────────────────────────────────


class TestAccountChangePolicy:
    def test_email_change_always_requires_approval(self):
        d = engine.evaluate(PolicyContext(action="email_change"))
        assert d.outcome == "approval_required"
        assert d.policy_id == "account_change_security"

    def test_address_change_always_requires_approval(self):
        d = engine.evaluate(PolicyContext(action="address_change"))
        assert d.outcome == "approval_required"


# ── Unknown action ────────────────────────────────────────────────────────────


class TestUnknownAction:
    def test_unknown_action_routes_to_human(self):
        d = engine.evaluate(PolicyContext(action="launch_rocket"))
        assert d.outcome == "approval_required"
        assert "launch_rocket" in d.reason


# ── PolicyDecision dataclass ──────────────────────────────────────────────────


class TestPolicyDecision:
    def test_outcome_values_are_valid(self):
        for outcome in ("auto_approve", "approval_required", "denied"):
            d = PolicyDecision(outcome=outcome, policy_id="test")
            assert d.outcome == outcome

    def test_eligibility_basis_captured(self):
        ctx = PolicyContext(
            action="issue_refund", amount=Decimal("30.00"), customer_segment="premium"
        )
        d = engine.evaluate(ctx)
        assert "amount" in d.eligibility_basis
