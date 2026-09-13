# ADR-008 — LLM Model Selection and Serving Architecture (Development)

**Status:** Proposed — pending domain benchmarking (LLM-003)  
**Date:** 2026-09-13  
**Deciders:** Engineering Lead  
**Supersedes:** —  
**Superseded by:** ADR-013 (production serving)

---

## Context

The agent requires an LLM for: intent understanding, response generation, tool-call decision-making, structured output production, and multi-turn conversation management (FR-001 through FR-019, LLM-001).

Requirements V1.1 §9 establishes a clear separation:
- **LLM-002**: Ollama is the development serving/runtime layer (local, self-hosted).
- **LLM-003**: 2–3 candidate open-weight models must be benchmarked before a final development model is selected.
- **LLM-004**: Production serving is a separate decision (ADR-013).
- **LLM-001**: Application logic must use an LLM abstraction interface — the agent is not coupled to a specific model or serving layer.

This ADR documents the **proposed development baseline model** (Llama 3.1 8B Instruct) that will be used for initial development and evaluated against alternatives. The final selection is confirmed after benchmarking.

The evaluation criteria from LLM-003:
1. Answer correctness on the domain-specific golden QA dataset
2. Tool-calling accuracy (function call schema compliance)
3. Structured-output reliability (Pydantic schema adherence)
4. RAG groundedness (does the model cite retrieved evidence faithfully?)
5. Agent task success (UC-01 through UC-12 completion rate)
6. Latency (P95 end-to-end response time)
7. VRAM / memory requirements
8. License (commercial use permitted?)
9. Inference cost per interaction

---

## Decision Drivers

| Driver | Weight | Notes |
|---|---|---|
| Tool-calling accuracy | High | Agent requires reliable function calling for order/customer/ticket tools |
| Structured output reliability | High | AgentDecision schema must be parseable every call |
| Open-weight / self-hostable | High | Project principle; must run via Ollama locally |
| Instruction following | High | Multi-step support workflows require reliable instruction compliance |
| Context window | Medium | Conversation history + retrieved chunks + tools ≥ 8K tokens |
| VRAM requirements | Medium | Development hardware constraint |
| License | High | Must permit commercial use |

---

## Considered Options

| Model | Tool calling | Struct. output | Context | VRAM | License | Notes |
|---|---|---|---|---|---|---|
| GPT-4o (OpenAI) | Excellent | Excellent | 128K | API-only | Proprietary | API dependency, cost, data residency |
| Claude 3.5 Sonnet (Anthropic) | Excellent | Excellent | 200K | API-only | Proprietary | API dependency, cost |
| **Llama 3.1 8B Instruct** | Good | Good | 128K | ~8GB | Meta Llama 3 Community | Strong baseline, Ollama native |
| Mistral 7B Instruct v0.3 | Good | Good | 32K | ~7GB | Apache 2.0 | Smaller context, good speed |
| Qwen 2.5 7B Instruct | Good | Good | 128K | ~7GB | Apache 2.0 | Strong multilingual; context competitive |
| Phi-3.5 Mini Instruct | Moderate | Good | 128K | ~4GB | MIT | Lower VRAM; weaker tool calling |

---

## Decision

**Propose Llama 3.1 8B Instruct** via Ollama as the V1 development baseline model, pending domain benchmarking results.

### Rationale for Proposing Llama 3.1 8B

- **Native tool calling**: Meta's Llama 3.1 release introduced native function calling support with a well-specified JSON tool-use format, directly relevant to the agent's tool invocation requirements.
- **128K context window**: accommodates 10-turn conversation history (FR-002), retrieved chunks (5× ~500 tokens), tool results, and the system prompt without context overflow.
- **Community support in Ollama**: `llama3.1:8b` is a first-class Ollama model with quantized variants available (Q4_K_M, Q5_K_M) that fit within 8–10GB VRAM.
- **License**: Meta Llama 3 Community License permits commercial use for services with fewer than 700M monthly active users — appropriate for this project.

### Benchmark Candidates

The following models will be benchmarked against the domain evaluation datasets before the final selection is confirmed:

1. **Llama 3.1 8B Instruct** (proposed baseline)
2. **Mistral 7B Instruct v0.3** (alternative: Apache 2.0, smaller context)
3. **Qwen 2.5 7B Instruct** (alternative: strong structured output, 128K context)

### Benchmark Protocol

Each candidate is evaluated on:
- `data/evaluation/golden_qa.jsonl` (70 QA pairs) — answer correctness
- `data/evaluation/agent_eval.jsonl` (50 agent scenarios) — task success, tool accuracy
- `data/evaluation/retrieval_eval.jsonl` (100 queries) — groundedness with top-5 retrieved chunks
- Latency: P50, P95 over 50 warmup queries on development hardware

Results are recorded in `experiments/llm_benchmarks/` and referenced in an ADR update before Phase 11.

### LLM Abstraction Interface (LLM-001)

```python
class LLMClient(Protocol):
    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDef] | None = None,
        response_format: type[BaseModel] | None = None,
    ) -> LLMResponse: ...
```

The `OllamaClient` implements this interface. Switching to a different model or serving layer requires only changing the concrete implementation, not application code.

---

## Consequences

**Positive:**
- Llama 3.1 8B runs in ~8GB VRAM (Q4_K_M quantization on consumer GPU or CPU-only at slower speed) — compatible with development hardware.
- 128K context window eliminates context overflow as a development concern.
- Ollama provides a simple REST API (`/api/chat`) that the `OllamaClient` wraps.
- Benchmarking 3 models before Phase 11 produces an ADR-grounded model selection rather than an arbitrary default.

**Negative / Trade-offs:**
- Local inference is slower than API-based models: expect 1–5 tokens/second on CPU, 20–50 tokens/second on consumer GPU. This affects end-to-end latency in development but not production (ADR-013).
- Llama 3.1 tool-calling format differs from the OpenAI standard; the `LLMClient` abstraction must normalize this.
- The Llama 3 Community License prohibits using Llama outputs to train competing foundation models — this does not affect support use cases.

**Risks and Mitigations:**
- Tool-calling reliability below threshold: mitigated by benchmarking against `agent_eval.jsonl` before committing to Phase 11; if reliability is insufficient, structured-output retry logic (LLM-005 prompt management) provides a fallback.
- Quantization artifacts reducing output quality: mitigated by testing Q4_K_M and Q5_K_M variants; Q5 is preferred if VRAM permits.

---

## Review Triggers

Revisit this ADR when:
- Domain benchmarking (LLM-003) is complete — update status to Accepted with the winning model.
- A new Llama or Mistral release materially outperforms the benchmarked candidates on tool-calling or structured output.
- Production serving (ADR-013) reveals a serving-side constraint that forces a model change.
