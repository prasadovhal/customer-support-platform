from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, NotFoundError
from app.db.session import get_db
from app.models.approval import ApprovalAuditLog, ApprovalRequest
from app.schemas.approval import ApprovalDecision, ApprovalResponse
from app.schemas.auth import TokenPayload
from app.security.dependencies import get_current_agent, get_current_token

router = APIRouter(prefix="/approvals", tags=["approvals"])

# Maps the approval action prefix to the required agent scope.
_ACTION_SCOPE_MAP: dict[str, str] = {
    "issue_refund": "approve:refunds",
    "cancel_order": "approve:cancellations",
    "email_change": "approve:account_changes",
    "address_change": "approve:account_changes",
}


def _required_scope_for(action: str) -> str:
    """Return the scope required to decide on a given action type."""
    for prefix, scope in _ACTION_SCOPE_MAP.items():
        if action.startswith(prefix):
            return scope
    return "approve:account_changes"  # default fallback


@router.get("/{approval_id}", response_model=ApprovalResponse)
async def get_approval(
    approval_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(get_current_token),
) -> ApprovalResponse:
    """Retrieve an approval request.

    Customers can view their own approvals; agents can view any.
    """
    result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if approval is None:
        raise NotFoundError(message=f"Approval {approval_id} not found.")

    if token.type == "customer":
        if str(approval.customer_id) != token.sub:
            raise AuthorizationError(
                message="You do not have access to this approval."
            )
    elif token.type != "agent":
        raise AuthorizationError(message="Unsupported token type.")

    return ApprovalResponse.model_validate(approval)


@router.post("/{approval_id}/decision", response_model=ApprovalResponse)
async def decide_approval(
    approval_id: uuid.UUID,
    body: ApprovalDecision,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(get_current_agent),
) -> ApprovalResponse:
    """Submit an approval decision (approve or deny).

    Agent only. The required scope depends on the action type:
    - issue_refund  → approve:refunds
    - cancel_order  → approve:cancellations
    - email_change / address_change → approve:account_changes

    The ApprovalRequest update and the ApprovalAuditLog insert are written
    in a single atomic transaction as required by ADR.
    """
    result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if approval is None:
        raise NotFoundError(message=f"Approval {approval_id} not found.")

    # Check that the agent has the correct scope for this action.
    required = _required_scope_for(approval.action)
    if required not in token.scopes:
        raise AuthorizationError(
            message=f"Missing required scope '{required}' for action '{approval.action}'."
        )

    now = datetime.now(timezone.utc)
    new_status = "approved" if body.decision == "approved" else "denied"

    # Single transaction: update approval + write audit log.
    async with db.begin_nested():
        approval.status = new_status
        approval.decided_by = token.sub
        approval.decided_at = now
        approval.decision_reason = body.reason

        audit_log = ApprovalAuditLog(
            id=uuid.uuid4(),
            approval_id=approval.id,
            event=body.decision,
            actor_id=token.sub,
            actor_role=token.type,
            reason=body.reason,
            policy_version=approval.policy_version,
        )
        db.add(audit_log)

    await db.refresh(approval)
    return ApprovalResponse.model_validate(approval)
