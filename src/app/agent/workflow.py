"""LangGraph-based support agent workflow (ADR-005).

Graph topology:
    classify_intent ──► retrieve_knowledge ──► handle_action ──► generate_response ──► END
                   └─────────────────────────────────────────────────────────────────────►
    (retrieve + handle_action skipped when needs_retrieval=False, e.g. greetings)
"""
from __future__ import annotations

import time
from typing import Any, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.llm import LLMClient, OllamaClient
from app.agent.prompts import SYSTEM_PROMPT, build_user_prompt
from app.agent.schemas import AgentResult, AgentState
from app.observability.metrics import (
    AGENT_CALLS,
    AGENT_LATENCY,
    LLM_CALLS,
    LLM_LATENCY,
    ML_INFERENCES,
    ML_LATENCY,
    RAG_LATENCY,
    RAG_RETRIEVALS,
)

# Intent labels that don't require knowledge retrieval
_GREETING_INTENTS = frozenset({"greeting", "thanks", "goodbye"})

# Intents that may trigger an approval request tool call
_ACTIONABLE_INTENTS = frozenset({"return_refund", "cancel_order"})

# Simple keyword heuristic when ML model is unavailable
_INTENT_KEYWORDS: dict[str, list[str]] = {
    "order_status":  ["order", "tracking", "shipped", "delivery", "track"],
    "return_refund": ["return", "refund", "exchange", "send back"],
    "cancel_order":  ["cancel", "cancellation", "cancel my order"],
    "billing":       ["charge", "invoice", "payment", "bill", "receipt"],
    "product_info":  ["product", "item", "spec", "warranty", "how does"],
    "shipping":      ["ship", "shipping", "address", "carrier", "estimated"],
    "account":       ["account", "password", "login", "email", "profile"],
    "escalation":    ["escalate", "supervisor", "manager", "not happy", "complaint"],
    "greeting":      ["hello", "hi", "hey", "thanks", "thank you", "bye"],
}

_FALLBACK_RESPONSE = (
    "I'm sorry, I wasn't able to process your request at this time. "
    "A support agent will follow up with you shortly."
)


# ─── Utility ─────────────────────────────────────────────────────────────────


def _keyword_intent(message: str) -> tuple[str, float]:
    lower = message.lower()
    for intent, keywords in _INTENT_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return intent, 0.6
    return "general_inquiry", 0.4


def _ml_intent(message: str) -> tuple[str, float]:
    t0 = time.perf_counter()
    try:
        from app.ml.predictor import TicketPredictor

        predictor = TicketPredictor()
        result = predictor.predict_category(
            subject=message[:200],
            body=message,
            customer_segment="standard",
        )
        ML_INFERENCES.labels(task="category", outcome="success").inc()
        ML_LATENCY.labels(task="category").observe(time.perf_counter() - t0)
        return result.category, float(result.confidence)
    except Exception:
        ML_INFERENCES.labels(task="category", outcome="no_model").inc()
        return _keyword_intent(message)


# ─── LangGraph nodes ─────────────────────────────────────────────────────────


def _make_classify_node():
    async def classify_intent(state: AgentState) -> dict[str, Any]:
        message = state.get("message", "")
        intent, confidence = _ml_intent(message)
        needs_retrieval = intent not in _GREETING_INTENTS
        logger.debug(f"classify: intent={intent} conf={confidence:.2f} retrieve={needs_retrieval}")
        return {
            "intent": intent,
            "intent_confidence": confidence,
            "category": intent,
            "needs_retrieval": needs_retrieval,
            "retrieved_doc_ids": [],
            "context_text": "",
            "sources": [],
            "tool_calls": [],
            "approval_result": None,
            "response": None,
            "error": None,
        }

    return classify_intent


def _make_retrieve_node(db: AsyncSession):
    async def retrieve_knowledge(state: AgentState) -> dict[str, Any]:
        if not state.get("needs_retrieval", True):
            return {}

        message = state.get("message", "")
        try:
            from app.api.v1.rag import _bm25_built, _get_pipeline

            pipeline = _get_pipeline()

            if not _bm25_built:
                retriever = pipeline._retriever
                await retriever.build_bm25_from_db(db)
                import app.api.v1.rag as _rag_module
                _rag_module._bm25_built = True

            t0 = time.perf_counter()
            rag_result = await pipeline.query(
                db=db,
                query=message,
                use_dense=True,
                use_bm25=True,
                use_reranker=True,
            )
            strategy = rag_result.retrieval_strategy
            RAG_RETRIEVALS.labels(strategy=strategy, outcome="success").inc()
            RAG_LATENCY.labels(strategy=strategy).observe(time.perf_counter() - t0)

            doc_ids = [c.doc_id for c in rag_result.chunks if c.doc_id]
            sources = [
                {
                    "doc_title": s.doc_title,
                    "doc_category": s.doc_category,
                    "doc_path": s.doc_path,
                    "doc_version": s.doc_version,
                    "chunk_index": s.chunk_index,
                }
                for s in rag_result.sources
            ]
            logger.debug(f"retrieve: {len(doc_ids)} docs, strategy={strategy}")
            return {
                "retrieved_doc_ids": doc_ids,
                "context_text": rag_result.context_text,
                "sources": sources,
                "tool_calls": state.get("tool_calls", []) + [
                    {"tool": "search_knowledge", "query": message, "n_results": len(doc_ids)}
                ],
            }
        except Exception as exc:
            RAG_RETRIEVALS.labels(strategy="hybrid", outcome="error").inc()
            logger.warning(f"RAG retrieval failed (proceeding without context): {exc}")
            return {"retrieved_doc_ids": [], "context_text": "", "sources": []}

    return retrieve_knowledge


def _make_handle_action_node(db: AsyncSession):
    """Check if the intent requires an approval action; if so, run it."""

    async def handle_action(state: AgentState) -> dict[str, Any]:
        intent = state.get("intent", "")
        customer_id = state.get("customer_id")
        conversation_id = state.get("conversation_id", "")
        order_id = state.get("order_id")

        if intent not in _ACTIONABLE_INTENTS or not customer_id:
            return {}

        # Map intent → approval action
        action_map = {
            "return_refund": "issue_refund",
            "cancel_order":  "cancel_order",
        }
        action = action_map.get(intent)
        if not action:
            return {}

        try:
            from app.agent.tools import request_approval

            approval = await request_approval(
                action=action,
                conversation_id=conversation_id,
                customer_id=customer_id,
                db=db,
                order_id=order_id,
                summary=state.get("message", "")[:200],
            )
            logger.debug(
                f"handle_action: {action} → outcome={approval.get('outcome')} "
                f"approval_id={approval.get('approval_id')}"
            )
            return {
                "approval_result": approval,
                "tool_calls": state.get("tool_calls", []) + [
                    {"tool": "request_approval", "action": action, **approval}
                ],
            }
        except Exception as exc:
            logger.warning(f"request_approval tool failed: {exc}")
            return {}

    return handle_action


def _make_generate_node(llm: LLMClient):
    async def generate_response(state: AgentState) -> dict[str, Any]:
        message = state.get("message", "")
        context = state.get("context_text", "")
        history = state.get("history", [])
        approval = state.get("approval_result")

        # Append approval outcome to context so LLM can reference it
        approval_note = ""
        if approval:
            outcome = approval.get("outcome", "")
            reason = approval.get("reason", "")
            if outcome == "auto_approve":
                approval_note = f"\n\n[System: Request automatically approved. {reason}]"
            elif outcome == "approval_required":
                approval_note = (
                    f"\n\n[System: Request is pending human approval "
                    f"(approval ID: {approval.get('approval_id')}). {reason}]"
                )
            elif outcome == "denied":
                approval_note = f"\n\n[System: Request denied by policy. {reason}]"

        full_context = context + approval_note

        messages: list[dict[str, str]] = history[-6:]
        user_prompt = build_user_prompt(message, full_context)
        messages.append({"role": "user", "content": user_prompt})

        from app.core.config import get_settings
        model = get_settings().OLLAMA_MODEL
        t0 = time.perf_counter()
        try:
            reply = await llm.chat(messages=messages, system=SYSTEM_PROMPT)
            LLM_CALLS.labels(model=model, outcome="success").inc()
            LLM_LATENCY.labels(model=model).observe(time.perf_counter() - t0)
        except Exception as exc:
            LLM_CALLS.labels(model=model, outcome="error").inc()
            logger.warning(f"LLM generation failed: {exc}")
            reply = _FALLBACK_RESPONSE

        groundedness: Optional[float] = None
        if context.strip():
            try:
                from app.evaluation.groundedness import _context_coverage
                groundedness = round(_context_coverage(reply, context), 4)
            except Exception:
                pass

        logger.debug(f"generate: {len(reply)} chars, groundedness={groundedness}")
        return {"response": reply, "groundedness_score": groundedness}

    return generate_response


# ─── Graph builder ────────────────────────────────────────────────────────────


def _build_graph(db: AsyncSession, llm: LLMClient) -> Any:
    from langgraph.graph import END, StateGraph

    graph = StateGraph(AgentState)

    graph.add_node("classify",      _make_classify_node())
    graph.add_node("retrieve",      _make_retrieve_node(db))
    graph.add_node("handle_action", _make_handle_action_node(db))
    graph.add_node("generate",      _make_generate_node(llm))

    graph.set_entry_point("classify")

    graph.add_conditional_edges(
        "classify",
        lambda s: "retrieve" if s.get("needs_retrieval", True) else "generate",
        {"retrieve": "retrieve", "generate": "generate"},
    )
    graph.add_edge("retrieve",      "handle_action")
    graph.add_edge("handle_action", "generate")
    graph.add_edge("generate",      END)

    return graph.compile()


# ─── Public entry point ───────────────────────────────────────────────────────


async def run_agent(
    message: str,
    conversation_id: str,
    customer_id: Optional[str],
    db: AsyncSession,
    history: Optional[list[dict[str, str]]] = None,
    order_id: Optional[str] = None,
    llm: Optional[LLMClient] = None,
) -> AgentResult:
    """Run the support agent workflow and return a structured result."""
    if llm is None:
        llm = OllamaClient()

    initial_state: AgentState = {
        "conversation_id": conversation_id,
        "customer_id": customer_id,
        "message": message,
        "history": history or [],
        "order_id": order_id,
        "intent": None,
        "intent_confidence": None,
        "category": None,
        "needs_retrieval": True,
        "retrieved_doc_ids": [],
        "context_text": "",
        "sources": [],
        "approval_result": None,
        "response": None,
        "groundedness_score": None,
        "tool_calls": [],
        "error": None,
    }

    t0 = time.perf_counter()
    try:
        app = _build_graph(db, llm)
        if hasattr(app, "ainvoke"):
            final_state: AgentState = await app.ainvoke(initial_state)
        else:
            import asyncio
            final_state = await asyncio.get_event_loop().run_in_executor(
                None, app.invoke, initial_state
            )
    except Exception as exc:
        logger.error(f"Agent workflow failed: {exc}")
        AGENT_CALLS.labels(intent="unknown", outcome="fallback").inc()
        AGENT_LATENCY.observe(time.perf_counter() - t0)
        return AgentResult(
            response=_FALLBACK_RESPONSE,
            latency_ms=int((time.perf_counter() - t0) * 1000),
        )

    latency_ms = int((time.perf_counter() - t0) * 1000)
    intent = final_state.get("intent") or "unknown"
    outcome = "fallback" if not final_state.get("response") else "success"
    AGENT_CALLS.labels(intent=intent, outcome=outcome).inc()
    AGENT_LATENCY.observe(time.perf_counter() - t0)

    return AgentResult(
        response=final_state.get("response") or _FALLBACK_RESPONSE,
        intent=final_state.get("intent"),
        intent_confidence=final_state.get("intent_confidence"),
        sources=final_state.get("sources", []),
        retrieved_doc_ids=final_state.get("retrieved_doc_ids", []),
        tool_calls=final_state.get("tool_calls", []),
        groundedness_score=final_state.get("groundedness_score"),
        latency_ms=latency_ms,
    )
