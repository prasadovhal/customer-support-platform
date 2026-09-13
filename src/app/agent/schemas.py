from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# TypedDict import compatible with Python 3.10+
try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """LangGraph workflow state for the support agent."""

    # Input
    conversation_id: str
    customer_id: Optional[str]
    message: str
    history: list[dict[str, str]]

    # Filled by classify node
    intent: Optional[str]
    intent_confidence: Optional[float]
    category: Optional[str]
    needs_retrieval: bool

    # Filled by retrieve node
    retrieved_doc_ids: list[str]
    context_text: str
    sources: list[dict[str, Any]]

    # Filled by generate node
    response: Optional[str]
    groundedness_score: Optional[float]
    tool_calls: list[dict[str, Any]]

    # Error passthrough
    error: Optional[str]


@dataclass
class AgentResult:
    """Structured result returned by run_agent to the API layer."""

    response: str
    intent: Optional[str] = None
    intent_confidence: Optional[float] = None
    sources: list[dict[str, Any]] = field(default_factory=list)
    retrieved_doc_ids: list[str] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    groundedness_score: Optional[float] = None
    latency_ms: int = 0
