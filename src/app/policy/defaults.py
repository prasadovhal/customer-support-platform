"""Default policy thresholds — applied when no active DB override exists."""
from __future__ import annotations

from decimal import Decimal

# Refund auto-approval thresholds by customer segment
REFUND_AUTO_THRESHOLD: dict[str, Decimal] = {
    "standard": Decimal("50.00"),
    "premium": Decimal("100.00"),
    "enterprise": Decimal("200.00"),
    "default": Decimal("50.00"),
}

# Number of days after delivery within which returns are eligible
RETURN_WINDOW_DAYS = 30

# Order statuses that allow automatic cancellation (no human needed)
CANCEL_AUTO_STATUSES = frozenset({"pending", "processing"})

# Order statuses that require human approval before cancellation
CANCEL_APPROVAL_STATUSES = frozenset({"shipped"})

# Order statuses where cancellation is not possible
CANCEL_DENIED_STATUSES = frozenset({"delivered", "cancelled", "refunded"})

# Policy version string — bump when defaults change
POLICY_VERSION = "1.0"
