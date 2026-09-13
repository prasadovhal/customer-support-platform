# ADR-013 — Production LLM Serving

**Status:** Accepted  
**Date:** 2026-09-13  
**Deciders:** Engineering Lead  
**Supersedes:** ADR-008 (development serving; Ollama remains the dev baseline)  
**Superseded by:** —

---

## Context

ADR-008 establishes Ollama as the **development** LLM serving layer and defers the production serving decision. Ollama is optimized for developer experience: easy model management, a simple REST API, and low operational overhead. It is not designed for production workloads with concurrent requests, strict latency SLOs, and high throughput requirements.

The platform's V1 production SLOs (§21):
- API P95 latency for synchronous operations: **< 3 seconds**
- End-to-end agent P95 latency: **< 8 seconds**

LLM inference is the largest latency contributor in the agent path. The production serving layer must:
1. Achieve the above latency targets under concurrent load.
2. Expose an API compatible with the `LLMClient` abstraction (LLM-001) without requiring application code changes.
3. Support the open-weight model selected through LLM-003 benchmarking.
4. Be self-hostable on a GPU instance (AWS EC2 G4dn/G5 or Hetzner GPU, ADR-011).
5. Provide health endpoints for ECS/Fargate health checks and circuit breaking (REL-007).

---

## Decision Drivers

| Driver | Weight | Notes |
|---|---|---|
| Throughput under concurrent requests | High | Concurrent agent calls during peak support hours |
| Latency (P95 token generation) | High | Direct impact on 8s SLO |
| OpenAI-compatible API | High | LLMClient abstraction (LLM-001) uses /v1/chat/completions |
| Open-source / self-hostable | High | Project principle |
| Tool calling / structured output support | High | Agent requires function calling |
| GPU memory efficiency | Medium | Must fit target model on available GPU |
| Operational complexity | Medium | Phase 26 deployment by a small team |

---

## Considered Options

| Option | Throughput | OAI-compat. | Tool calling | Self-hosted | GPU efficiency | Complexity |
|---|---|---|---|---|---|---|
| **vLLM** | Excellent | Yes | Yes | Yes | Excellent (PagedAttention) | Medium |
| Ollama (prod) | Poor | Partial | Limited | Yes | Moderate | Low |
| TGI (HuggingFace) | Good | Yes | Limited | Yes | Good | Medium |
| llama.cpp server | Moderate | Partial | Limited | Yes | Good (CPU/GGUF) | Low |
| Together AI | Excellent | Yes | Yes | No (managed) | N/A | Very low |
| Groq | Excellent | Yes | Yes | No (managed) | N/A | Very low |
| Replicate | Good | Partial | Limited | No | N/A | Low |

---

## Decision

Use **vLLM** as the self-hosted production LLM serving layer.

### Key Capabilities Used

- **PagedAttention**: GPU KV-cache memory management that dramatically increases throughput for concurrent requests compared to naive serving.
- **Continuous batching**: dynamically batches incoming requests, eliminating idle GPU time between requests.
- **OpenAI-compatible REST API** (`/v1/chat/completions`, `/v1/completions`): the existing `OllamaClient` can be replaced with a standard OpenAI-compatible client that points to the vLLM endpoint.
- **Tool calling**: supported for Llama 3.1 and compatible models via the `--tool-call-parser` argument.
- **Structured outputs**: JSON schema enforcement via `guided_json` parameter.

### Deployment Architecture

```
ECS Fargate (API/Worker)
      │ HTTP
      ▼
EC2 G4dn.xlarge (NVIDIA T4, 16GB VRAM)
  └── vLLM serving container
        Model: llama3.1:8b-instruct-q4 (or benchmark winner)
        Port: 8000
        OAI API: /v1/chat/completions

Health check: GET /health → 200 OK
```

### LLMClient Swap

```python
# Development (Ollama)
class OllamaClient(LLMClient):
    base_url = "http://localhost:11434"

# Production (vLLM)
class VLLMClient(LLMClient):
    base_url = "http://vllm-service:8000"
    # Same /v1/chat/completions API
```

The `LLMClient` abstraction (LLM-001) means no application code changes are required when switching from Ollama to vLLM.

### Circuit Breaking Integration (REL-007)

The vLLM `/health` endpoint is polled by the circuit breaker in the `LLMClient`. On repeated failures, the circuit opens and requests fall back to human escalation (UC-11) rather than hanging.

---

## Rationale

**Why vLLM over Ollama in production:**  
Ollama uses a naive serving model: each request is processed sequentially with no batching. Under concurrent load (multiple simultaneous agent requests), Ollama queues requests, causing latency spikes that violate the 8s P95 SLO. vLLM's PagedAttention + continuous batching delivers 10–30× higher throughput at equivalent GPU resources.

**Why vLLM over TGI:**  
Both are strong production serving options. vLLM was chosen due to: broader Llama 3.x tool-calling support (the benchmark winner from ADR-008), larger community for troubleshooting, and cleaner OpenAI API compatibility including the `guided_json` structured output feature.

**Why self-hosted over Together AI / Groq:**  
Managed inference services introduce: per-token cost at scale, network latency for every LLM call, data residency concerns (customer query content sent to a third party), and a hard external dependency that cannot be circuit-broken to a local fallback. Self-hosted vLLM has higher operational overhead but meets the project's reliability, cost, and data-residency requirements.

**Why not llama.cpp server:**  
llama.cpp's GGUF quantization enables CPU inference, which is valuable for development and very low-volume use cases. For production throughput at the SLO targets, GPU-accelerated serving with PagedAttention is necessary.

---

## Consequences

**Positive:**
- PagedAttention allows a single G4dn.xlarge (T4, 16GB VRAM) to serve Llama 3.1 8B at production concurrency without memory fragmentation.
- OpenAI-compatible API: `OllamaClient` is replaced by a `VLLMClient` with identical interface; no agent code changes.
- Tool calling and structured output (guided_json) support meets FR-013 and PHASE-13 structured output requirements.
- Apache 2.0 license; open-source with strong community support.
- Health endpoint enables ECS health checks and circuit breaking (REL-007).

**Negative / Trade-offs:**
- vLLM requires a GPU instance: EC2 G4dn.xlarge costs ~$0.53/hour on-demand (~$380/month). Spot instances reduce this by 60–70% for batch workloads.
- vLLM container image is large (~5GB); ECR pull time during ECS task startup must be accounted for in deployment planning.
- Model weights must be downloaded/cached on the EC2 instance or stored in S3 and loaded at startup.
- Operational complexity is higher than managed inference: GPU driver management, CUDA version pinning, OOM handling.

**Risks and Mitigations:**
- GPU OOM during peak concurrency: mitigated by configuring `--max-model-len` and `--gpu-memory-utilization` conservatively (0.85) to leave headroom for KV cache growth.
- vLLM tool-calling format divergence from Ollama format: mitigated by integration testing the `VLLMClient` against the agent evaluation suite (`agent_eval.jsonl`) before Phase 26 deployment.
- EC2 instance failure: mitigated by auto-scaling group with minimum 1 instance; circuit breaker provides LLM-unavailable fallback to human escalation (UC-11).

---

## Review Triggers

Revisit this ADR if:
- vLLM latency benchmarks during Phase 26 show the 8s P95 SLO is not met on the target GPU instance.
- A managed inference provider (e.g., Amazon Bedrock with Llama 3.1) offers acceptable data-residency guarantees and competitive cost.
- The selected benchmark model (ADR-008) is not yet supported by vLLM's tool-calling parser.
