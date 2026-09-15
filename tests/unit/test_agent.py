"""Unit tests for the Phase 11 agent components.

All DB and LLM interactions are mocked so tests run without any external services.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import all models upfront so SQLAlchemy can resolve the full relationship graph
# before any mapper configuration is triggered by individual model imports.
import app.models.product  # noqa: F401
import app.models.knowledge  # noqa: F401

# ─── LLM client ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ollama_client_chat_success():
    from app.agent.llm import OllamaClient

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "message": {"role": "assistant", "content": "Here is your answer."}
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        instance.post = AsyncMock(return_value=mock_response)
        MockClient.return_value = instance

        client = OllamaClient()
        result = await client.chat(
            messages=[{"role": "user", "content": "Hello"}],
            system="You are helpful.",
        )

    assert result == "Here is your answer."


# ─── Prompts ─────────────────────────────────────────────────────────────────


def test_build_user_prompt_with_context():
    from app.agent.prompts import build_user_prompt

    prompt = build_user_prompt(
        "What is the return policy?", "Returns allowed within 30 days."
    )
    assert "return policy" in prompt.lower()
    assert "30 days" in prompt


def test_build_user_prompt_no_context():
    from app.agent.prompts import build_user_prompt

    prompt = build_user_prompt("What is the return policy?", "")
    assert "return policy" in prompt.lower()
    assert "no relevant" in prompt.lower() or "not found" in prompt.lower()


# ─── Tools ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_customer_found():
    from app.agent.tools import get_customer

    cid = uuid.uuid4()
    mock_customer = MagicMock()
    mock_customer.id = cid
    mock_customer.name = "Alice"
    mock_customer.email = "alice@example.com"
    mock_customer.customer_segment = "premium"
    mock_customer.account_status = "active"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_customer

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await get_customer(str(cid), mock_db)

    assert result is not None
    assert result["email"] == "alice@example.com"
    assert result["customer_segment"] == "premium"


@pytest.mark.asyncio
async def test_get_customer_not_found():
    from app.agent.tools import get_customer

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await get_customer(str(uuid.uuid4()), mock_db)
    assert result is None


@pytest.mark.asyncio
async def test_get_order_found():
    from app.agent.tools import get_order

    oid = uuid.uuid4()
    import datetime
    from decimal import Decimal

    mock_order = MagicMock()
    mock_order.id = oid
    mock_order.order_number = "ORD-00123"
    mock_order.status = "shipped"
    mock_order.total_amount = Decimal("49.99")
    mock_order.currency = "USD"
    mock_order.tracking_number = "1Z999AA10123456784"
    mock_order.carrier = "UPS"
    mock_order.shipped_at = datetime.datetime(2024, 1, 15, tzinfo=datetime.timezone.utc)
    mock_order.delivered_at = None

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_order

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await get_order(str(oid), mock_db)

    assert result is not None
    assert result["order_number"] == "ORD-00123"
    assert result["status"] == "shipped"
    assert result["tracking_number"] == "1Z999AA10123456784"
    assert result["shipped_at"] is not None


@pytest.mark.asyncio
async def test_create_ticket():
    from app.agent.tools import create_ticket

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()

    result = await create_ticket(
        customer_id=str(uuid.uuid4()),
        conversation_id=str(uuid.uuid4()),
        category="returns",
        priority="P2",
        summary="Customer wants to return a defective item.",
        db=mock_db,
    )

    assert result["status"] == "open"
    assert result["ticket_number"].startswith("TK-")
    assert len(result["ticket_number"]) == 8  # TK- + 5 hex chars


# ─── Keyword intent heuristic ─────────────────────────────────────────────────


def test_keyword_intent_order():
    from app.agent.workflow import _keyword_intent

    intent, conf = _keyword_intent("Where is my order?")
    assert intent == "order_status"
    assert conf > 0


def test_keyword_intent_return():
    from app.agent.workflow import _keyword_intent

    intent, conf = _keyword_intent("I want to return this item")
    assert intent == "return_refund"


def test_keyword_intent_greeting():
    from app.agent.workflow import _keyword_intent

    intent, conf = _keyword_intent("Hello, I need help")
    assert intent == "greeting"


def test_keyword_intent_fallback():
    from app.agent.workflow import _keyword_intent

    intent, conf = _keyword_intent("xyzzy random text")
    assert intent == "general_inquiry"


# ─── Workflow integration (mocked LLM + RAG) ─────────────────────────────────


@pytest.mark.asyncio
async def test_run_agent_llm_failure_returns_fallback():
    """When the LLM raises, run_agent should return the fallback response."""
    from app.agent.workflow import run_agent, _FALLBACK_RESPONSE

    class FailingLLM:
        async def chat(self, messages, system=None):
            raise RuntimeError("LLM unavailable")

    mock_db = AsyncMock()
    # Make RAG retrieval fail gracefully too
    mock_db.execute = AsyncMock(side_effect=Exception("DB unavailable"))

    result = await run_agent(
        message="What is the return policy?",
        conversation_id=str(uuid.uuid4()),
        customer_id=None,
        db=mock_db,
        llm=FailingLLM(),
    )

    assert result.response == _FALLBACK_RESPONSE
    assert result.latency_ms >= 0


@pytest.mark.asyncio
async def test_run_agent_greeting_skips_retrieval():
    """Greeting intent should skip retrieval and go straight to generate."""
    from app.agent.workflow import run_agent

    generated_reply = "Hello! How can I help you today?"

    class MockLLM:
        async def chat(self, messages, system=None):
            return generated_reply

    mock_db = AsyncMock()

    # Pin intent so the test is not sensitive to which ML model is loaded on disk.
    with patch("app.agent.workflow._ml_intent", return_value=("greeting", 0.95)):
        result = await run_agent(
            message="Hello there",
            conversation_id=str(uuid.uuid4()),
            customer_id=None,
            db=mock_db,
            llm=MockLLM(),
        )

    assert result.response == generated_reply
    assert result.intent == "greeting"
    assert result.retrieved_doc_ids == []


@pytest.mark.asyncio
async def test_run_agent_with_rag_context():
    """Non-greeting should attempt retrieval; mock RAG returning context."""
    from app.agent.workflow import run_agent

    answer = "You can return within 30 days of purchase."

    class MockLLM:
        async def chat(self, messages, system=None):
            return answer

    mock_db = AsyncMock()

    # Patch _get_pipeline so RAG doesn't try to hit a real DB
    mock_rag_result = MagicMock()
    mock_rag_result.context_text = "Returns are allowed within 30 days."
    mock_rag_result.chunks = []
    mock_rag_result.sources = []
    mock_rag_result.retrieval_strategy = "bm25"

    mock_pipeline = AsyncMock()
    mock_pipeline.query = AsyncMock(return_value=mock_rag_result)
    mock_pipeline._retriever = MagicMock()
    mock_pipeline._retriever.build_bm25_from_db = AsyncMock()

    with patch("app.api.v1.rag._get_pipeline", return_value=mock_pipeline), patch(
        "app.api.v1.rag._bm25_built", True
    ):
        result = await run_agent(
            message="What is the return policy?",
            conversation_id=str(uuid.uuid4()),
            customer_id=None,
            db=mock_db,
            llm=MockLLM(),
        )

    assert result.response == answer
    assert result.intent is not None


@pytest.mark.asyncio
async def test_run_agent_result_fields():
    """AgentResult should have all expected fields with correct types."""
    from app.agent.workflow import run_agent

    class EchoLLM:
        async def chat(self, messages, system=None):
            return "Acknowledged."

    mock_db = AsyncMock()

    result = await run_agent(
        message="Hi",
        conversation_id=str(uuid.uuid4()),
        customer_id=None,
        db=mock_db,
        llm=EchoLLM(),
    )

    assert isinstance(result.response, str)
    assert isinstance(result.retrieved_doc_ids, list)
    assert isinstance(result.tool_calls, list)
    assert isinstance(result.sources, list)
    assert isinstance(result.latency_ms, int)
    assert result.latency_ms >= 0
