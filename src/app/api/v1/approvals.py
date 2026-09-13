from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AuthorizationError, ConflictError, NotFoundError, ValidationError
from app.db.session import get_db
from app.models.approval import ApprovalAuditLog, ApprovalRequest
from app.models.conversation import Conversation, ConversationWorkflowState
from app.models.customer import Customer
from app.models.order import Order
from app.policy.engine import PolicyContext, PolicyEngine
from app.schemas.approval import ApprovalCreate, ApprovalDecision, ApprovalResponse
from app.schemas.auth import TokenPayload
from app.security.dependencies import get_current_agent, get_current_token

router = APIRouter(prefix="/approvals", tags=["approvals"])

_policy_engine = PolicyEngine()

_ACTION_SCOPE_MAP: dict[str, str] = {
    "issue_refund":   "approve:refunds",
    "cancel_order":   "approve:cancellations",
    "email_change":   "approve:account_changes",
    "address_change": "approve:account_changes",
}


def _required_scope_for(action: str) -> str:
    for prefix, scope in _ACTION_SCOPE_MAP.items():
        if action.startswith(prefix):
            return scope
    return "approve:account_changes"


def _sla_deadline() -> datetime:
    hours = get_settings().APPROVAL_SLA_HOURS
    return datetime.now(timezone.utc) + timedelta(hours=hours)


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("", response_model=ApprovalResponse, status_code=201)
async def create_approval(
    body: ApprovalCreate,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(get_current_token),
) -> ApprovalResponse:
    """Request an action that may require human approval.

    Steps:
    1. Verify conversation access.
    2. Load order / customer context for policy evaluation.
    3. Run the policy engine — may auto-approve, pend, or deny.
    4. Persist ApprovalRequest + ApprovalAuditLog atomically.
    5. If pending, update ConversationWorkflowState.
    """
    # 1. Idempotency — check if already submitted
    existing = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.idempotency_key == body.idempotency_key)
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(message="An approval with this idempotency_key already exists.")

    # 2. Load conversation and check access
    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == body.conversation_id)
    )
    conv = conv_result.scalar_one_or_none()
    if conv is None:
        raise NotFoundError(message=f"Conversation {body.conversation_id} not found.")

    if token.type == "customer":
        if conv.customer_id is None or str(conv.customer_id) != token.sub:
            raise AuthorizationError(message="You do not have access to this conversation.")
    elif token.type != "agent":
        raise AuthorizationError(message="Unsupported token type.")

    customer_id = conv.customer_id
    if customer_id is None:
        raise ValidationError(message="Conversation has no associated customer.")

    # 3. Load customer segment for policy threshold
    cust_result = await db.execute(
        select(Customer.customer_segment).where(Customer.id == customer_id)
    )
    customer_segment: str = cust_result.scalar_one_or_none() or "standard"

    # 4. Load order context if provided
    order_status: str | None = None
    order_age_days: int | None = None
    if body.order_id:
        order_result = await db.execute(
            select(Order).where(Order.id == body.order_id)
        )
        order = order_result.scalar_one_or_none()
        if order is None:
            raise NotFoundError(message=f"Order {body.order_id} not found.")
        order_status = order.status
        if order.created_at:
            order_age_days = (datetime.now(timezone.utc) - order.created_at.replace(tzinfo=timezone.utc)).days

    # 5. Run policy engine
    ctx = PolicyContext(
        action=body.action,
        amount=body.amount,
        currency=body.currency,
        order_status=order_status,
        customer_segment=customer_segment,
        order_age_days=order_age_days,
    )
    decision = _policy_engine.evaluate(ctx)

    if decision.outcome == "denied":
        raise ValidationError(
            message=f"Action denied by policy: {decision.reason}",
            detail={"policy_id": decision.policy_id, "policy_version": decision.policy_version},
        )

    # 6. Map outcome to approval status
    status_map = {
        "auto_approve":       "approved",
        "approval_required":  "pending_approval",
    }
    approval_status = status_map[decision.outcome]
    now = datetime.now(timezone.utc)

    # 7. Persist ApprovalRequest + audit log atomically
    approval = ApprovalRequest(
        id=uuid.uuid4(),
        action=body.action,
        status=approval_status,
        customer_id=customer_id,
        conversation_id=body.conversation_id,
        order_id=body.order_id,
        amount=body.amount,
        currency=body.currency,
        policy_id=decision.policy_id,
        policy_version=decision.policy_version,
        eligibility_basis=decision.eligibility_basis,
        requested_at=now,
        sla_deadline=_sla_deadline(),
        idempotency_key=body.idempotency_key,
        # For auto-approvals, record immediate decision
        decided_by=token.sub if decision.outcome == "auto_approve" else None,
        decided_at=now if decision.outcome == "auto_approve" else None,
        decision_reason=decision.reason if decision.outcome == "auto_approve" else None,
    )
    db.add(approval)

    audit_log = ApprovalAuditLog(
        id=uuid.uuid4(),
        approval_id=approval.id,
        event="requested" if decision.outcome == "approval_required" else "auto_approved",
        actor_id=token.sub,
        actor_role=token.type,
        reason=decision.reason,
        policy_version=decision.policy_version,
    )
    db.add(audit_log)

    # 8. Update ConversationWorkflowState if pending
    if decision.outcome == "approval_required":
        wf_result = await db.execute(
            select(ConversationWorkflowState).where(
                ConversationWorkflowState.conversation_id == body.conversation_id
            )
        )
        wf = wf_result.scalar_one_or_none()
        if wf:
            wf.state = "awaiting_approval"
            wf.pending_approval_id = approval.id
        else:
            db.add(ConversationWorkflowState(
                id=uuid.uuid4(),
                conversation_id=body.conversation_id,
                state="awaiting_approval",
                pending_approval_id=approval.id,
            ))

    await db.flush()
    await db.refresh(approval)

    return ApprovalResponse(
        id=approval.id,
        action=approval.action,
        status=approval.status,
        amount=approval.amount,
        currency=approval.currency,
        policy_outcome=decision.outcome,
        policy_id=decision.policy_id,
        reason=decision.reason,
        requested_at=approval.requested_at,
        sla_deadline=approval.sla_deadline,
        decided_at=approval.decided_at,
        decided_by=approval.decided_by,
        decision_reason=approval.decision_reason,
    )


# ── Read ──────────────────────────────────────────────────────────────────────

@router.get("/{approval_id}", response_model=ApprovalResponse)
async def get_approval(
    approval_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(get_current_token),
) -> ApprovalResponse:
    """Retrieve an approval request. Customers see their own; agents see any."""
    result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if approval is None:
        raise NotFoundError(message=f"Approval {approval_id} not found.")

    if token.type == "customer":
        if str(approval.customer_id) != token.sub:
            raise AuthorizationError(message="You do not have access to this approval.")
    elif token.type != "agent":
        raise AuthorizationError(message="Unsupported token type.")

    return ApprovalResponse(
        id=approval.id,
        action=approval.action,
        status=approval.status,
        amount=approval.amount,
        currency=approval.currency,
        requested_at=approval.requested_at,
        sla_deadline=approval.sla_deadline,
        decided_at=approval.decided_at,
        decided_by=approval.decided_by,
        decision_reason=approval.decision_reason,
    )


# ── Decide ────────────────────────────────────────────────────────────────────

@router.post("/{approval_id}/decision", response_model=ApprovalResponse)
async def decide_approval(
    approval_id: uuid.UUID,
    body: ApprovalDecision,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(get_current_agent),
) -> ApprovalResponse:
    """Submit an approve/deny decision. Agent only; scope checked per action type."""
    result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if approval is None:
        raise NotFoundError(message=f"Approval {approval_id} not found.")

    if approval.status not in ("pending_approval", "action_requested"):
        raise ValidationError(
            message=f"Cannot decide on approval in status '{approval.status}'."
        )

    required = _required_scope_for(approval.action)
    if required not in token.scopes:
        raise AuthorizationError(
            message=f"Missing required scope '{required}' for action '{approval.action}'."
        )

    now = datetime.now(timezone.utc)
    new_status = "approved" if body.decision == "approved" else "denied"

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

        # Clear the workflow state pending flag if approved/denied
        wf_result = await db.execute(
            select(ConversationWorkflowState).where(
                ConversationWorkflowState.conversation_id == approval.conversation_id
            )
        )
        wf = wf_result.scalar_one_or_none()
        if wf and str(wf.pending_approval_id) == str(approval.id):
            wf.state = "active"
            wf.pending_approval_id = None

    await db.refresh(approval)
    return ApprovalResponse(
        id=approval.id,
        action=approval.action,
        status=approval.status,
        amount=approval.amount,
        currency=approval.currency,
        requested_at=approval.requested_at,
        sla_deadline=approval.sla_deadline,
        decided_at=approval.decided_at,
        decided_by=approval.decided_by,
        decision_reason=approval.decision_reason,
    )
