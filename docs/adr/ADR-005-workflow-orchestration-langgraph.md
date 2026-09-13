# ADR-005 — Workflow Orchestration: LangGraph

**Status:** Accepted (evaluate against alternatives at Phase 22 experimentation)  
**Date:** 2026-09-07  
**Deciders:** Engineering Lead  
**Supersedes:** —  
**Superseded by:** —

---

## Context

The agent requires a stateful workflow orchestration layer to manage multi-step, branching support workflows. The requirements and use-case specifications define workflows that include:

- **Branching logic** — different paths based on intent, eligibility, risk classification.
- **Durable state** — approval and re-verification states must survive service restarts.
- **Human-in-the-loop** — workflows pause and resume when a human approves or submits a verification code.
- **Retries** — LLM calls and tool calls may fail transiently and need bounded retry.
- **State inspection** — workflow state must be observable for debugging and audit.
- **Multi-turn continuity** — a workflow started in one turn must be resumable in a later turn within the same conversation.

The orchestration layer sits between the API layer and the LLM/tool layer. It determines what happens next at each step — not the LLM.

---

## Decision Drivers

| Driver | Weight | Notes |
|---|---|---|
| Stateful graph-based workflows | High | Approval + re-verification require persistent state graphs |
| Human-in-the-loop (pause/resume) | High | Core requirement for UC-04, UC-05, UC-06 |
| Python-native | High | Entire stack is Python |
| Checkpointing / durability | High | Workflow state must survive restarts |
| Agent-specific primitives | High | Tool calling, structured output, retry patterns |
| Debuggability / observability | Medium | Must be able to inspect state at any node |
| Overhead / complexity | Medium | Should not over-engineer for V1 single-agent baseline |
| Community and maintenance | Medium | Not a dead project |
| Avoids LLM-centric lock-in | High | Orchestration logic must not be inside the LLM |

---

## Considered Options

### Option A — LangGraph

Graph-based stateful workflow framework from LangChain ecosystem. Defines workflows as directed graphs of nodes (functions) with typed state. Supports checkpointing, human-in-the-loop interrupts, and streaming.

**Pros:**
- Purpose-built for stateful agentic workflows with human-in-the-loop.
- Native checkpointing via configurable backends (PostgreSQL checkpointer available).
- Graph definition is explicit Python code — inspectable, testable.
- `interrupt()` primitive for human approval pauses — maps directly to the approval workflow.
- Active development, growing ecosystem.
- LLM-agnostic (works with any LLM behind the abstraction layer).

**Cons:**
- Part of the LangChain ecosystem — introduces LangChain as a dependency even if other LangChain components are not used.
- Relatively young (API stability risk for non-LTS versions).
- Graph definition style requires learning curve.
- Some features (streaming UI, LangSmith tracing) are ecosystem-specific.

### Option B — Custom Finite State Machine (pure Python)

Implement the workflow as a custom FSM using Python dataclasses, enums, and a dispatcher.

**Pros:**
- Zero dependencies beyond Python standard library.
- Full control over state representation and serialization.
- No framework lock-in.

**Cons:**
- Must implement checkpointing, durability, retry logic, and human-in-the-loop from scratch.
- Significant boilerplate for every new workflow.
- No graph visualization or standard debugging tools.
- High ongoing maintenance burden as new intents/workflows are added.

### Option C — Temporal

Distributed workflow orchestration platform. Workflows are durable functions; state is implicit in the workflow execution history.

**Pros:**
- Production-grade durability and reliability.
- Long-running workflows (hours, days) are natively supported.
- Excellent human-in-the-loop support via signals.
- Strong observability (Temporal UI).

**Cons:**
- Requires a dedicated Temporal server — additional service in the stack.
- Substantial operational complexity for V1.
- Designed for workflows that run for days; our V1 workflows complete in minutes to hours.
- Learning curve significantly higher than LangGraph for AI-specific patterns.
- Overkill for V1 single-agent baseline.

### Option D — Celery as Workflow Orchestrator

Use Celery chains and chords to compose multi-step workflows.

**Pros:**
- Already in the stack for async processing.
- No additional dependency.

**Cons:**
- Celery is a task queue, not a workflow orchestrator. It lacks: typed state, graph-based branching, human-in-the-loop primitives, LLM-specific retry patterns.
- Approval state management would require custom logic identical to building Option B.
- Debugging complex chains is difficult.
- Not designed for agent-style iterative reasoning loops.

### Option E — Prefect

Data workflow orchestration tool.

**Pros:**
- Good for data pipelines.

**Cons:**
- Designed for batch data pipelines, not conversational AI workflows.
- No agent-specific primitives.
- Overkill operational footprint for this use case.

---

## Decision

**Use LangGraph** for stateful agent workflow orchestration.

Specific configuration:
- Define each intent-workflow as a `StateGraph` with typed state (Python dataclasses or TypedDict).
- Use **PostgreSQL as the checkpointer backend** (`langgraph-checkpoint-postgres`) so workflow state is durable and survives restarts.
- Use LangGraph's `interrupt()` for human-in-the-loop pauses (approval, re-verification).
- Define the LLM interaction as a node in the graph — not the controller of the graph.
- Keep the graph definition in the Agent Service; the LLM is called by graph nodes but does not determine graph transitions.

---

## Rationale

**Why LangGraph over custom FSM:**
The human-in-the-loop interrupt + PostgreSQL checkpointer combination gives us durable, resumable workflows with essentially zero infrastructure added (reuses the existing PostgreSQL instance). Implementing equivalent durability from scratch would require weeks of boilerplate and carry higher risk of edge-case bugs in the approval state machine.

**Why LangGraph over Temporal:**
Temporal requires a dedicated server and an ops learning curve disproportionate to V1 needs. Our workflows run for minutes to hours (approval SLA is 4 business hours) — Temporal's strength is weeks-long workflows. LangGraph's PostgreSQL checkpointer provides sufficient durability for V1.

**Why LangGraph over Celery-as-orchestrator:**
Celery lacks graph-based branching, typed state, and human-in-the-loop primitives. Using it for orchestration would produce unmaintainable code.

**Architectural constraint — LLM does not control graph transitions:**
Per architecture principle P-02, the LLM recommends actions; application logic (the graph) controls what happens next. The LLM is a node in the graph, not the graph controller.

---

## Implementation Pattern

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from typing import TypedDict, Literal

class RefundWorkflowState(TypedDict):
    conversation_id: str
    customer_id: str
    order_id: str | None
    intent: str | None
    order_data: dict | None
    policy_data: dict | None
    eligibility: bool | None
    refund_amount: float | None
    approval_id: str | None
    approval_state: Literal[
        "not_required", "pending", "approved", "denied", "timeout"
    ] | None
    response: str | None

# Graph nodes: each is a pure Python function
# Graph edges: Python conditionals — not LLM decisions
graph = StateGraph(RefundWorkflowState)
graph.add_node("classify_intent", classify_intent_node)
graph.add_node("fetch_order", fetch_order_node)
graph.add_node("check_eligibility", check_eligibility_node)
graph.add_node("request_approval", request_approval_node)
graph.add_node("await_approval", await_approval_node)   # uses interrupt()
graph.add_node("execute_refund", execute_refund_node)
graph.add_node("generate_response", generate_response_node)

# Conditional edge — Python logic, not LLM
graph.add_conditional_edges(
    "check_eligibility",
    lambda state: "request_approval" if state["eligibility"] else "generate_response"
)
```

**Checkpointer setup:**
```python
checkpointer = PostgresSaver.from_conn_string(DATABASE_URL)
app = graph.compile(checkpointer=checkpointer)

# Resume mid-workflow (e.g., after human approval):
config = {"configurable": {"thread_id": conversation_id}}
result = app.invoke({"approval_state": "approved"}, config=config)
```

---

## Consequences

**Positive:**
- Approval and re-verification workflows are durable by default — PostgreSQL checkpointer handles restarts.
- Human-in-the-loop is a first-class primitive, not a workaround.
- Graph definition is inspectable, testable as pure Python functions.
- New workflows (new intents) are new `StateGraph` definitions — no framework changes.
- LangGraph's streaming mode enables real-time agent step visibility in traces.

**Negative / Trade-offs:**
- LangChain ecosystem dependency — if LangGraph undergoes breaking API changes, migration effort is required.
- Graph definition style requires team familiarity.
- PostgreSQL checkpointer writes workflow state on every node transition — adds DB write load (acceptable at V1 scale).

---

## Experiment Plan (Phase 22)

At Phase 22 (Experimentation), evaluate LangGraph against:
- Custom lightweight FSM (for simpler workflows that don't need checkpointing).
- Temporal (if scale or reliability requirements increase).

Evaluation criteria: workflow correctness, restart recovery time, human-in-the-loop reliability, observability, maintenance burden.

---

## Review Triggers

Revisit this ADR if:
- LangGraph introduces breaking API changes that require significant rework.
- Approval workflow reliability issues are traced to the checkpointer.
- Scale requires distributed workflow execution (multiple agent workers coordinating).
- Multi-agent architecture is adopted (Phase 22 experiment) — Temporal may become preferable.
