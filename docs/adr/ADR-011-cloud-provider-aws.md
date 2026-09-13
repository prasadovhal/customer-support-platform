# ADR-011 — Cloud Provider and Deployment Target

**Status:** Accepted  
**Date:** 2026-09-13  
**Deciders:** Engineering Lead  
**Supersedes:** —  
**Superseded by:** —

---

## Context

The platform requires a cloud deployment target for Phase 26 that supports: Linux containers, PostgreSQL, self-hosted retrieval/vector infrastructure, asynchronous processing (Redis + Celery), secret management, TLS termination, and persistent storage (§23 Deployment Requirements).

An additional constraint is the LLM serving layer (ADR-008, ADR-013): the production LLM serving decision (vLLM, ADR-013) requires GPU instances, which materially influences cloud provider economics.

The project is designed to be **cloud-portable**: containers, environment-variable configuration, and infrastructure-as-code (ADR-012) mean migration is feasible. The cloud provider decision determines the default path, not an irreversible lock-in.

---

## Decision Drivers

| Driver | Weight | Notes |
|---|---|---|
| GPU instance availability | High | vLLM production serving requires GPU (ADR-013) |
| Container orchestration maturity | High | ECS/EKS/GKE for API and worker services |
| Managed PostgreSQL | High | Avoid self-managing database primary/replica |
| Managed Redis | High | ElastiCache / Memorystore for Celery broker |
| Secret management | High | Secrets Manager / Secret Manager for SEC-004 |
| Ecosystem / tooling breadth | Medium | IAM, VPC, ECR, CloudWatch |
| Cost at development scale | Medium | Phase 26 is a learning/portfolio deployment |
| Open-source compatibility | Medium | Must support self-hosted pgvector, Jaeger, etc. |
| IaC provider support | Medium | OpenTofu (ADR-012) must have stable providers |

---

## Considered Options

| Provider | GPU instances | Managed PG | Managed Redis | Container orch. | Strengths | Weaknesses |
|---|---|---|---|---|---|---|
| **AWS** | EC2 G/P series | RDS PostgreSQL | ElastiCache | ECS Fargate / EKS | Largest ecosystem; strongest OpenTofu support | Higher cost; complexity |
| GCP | GCE A100/T4 | Cloud SQL | Memorystore | Cloud Run / GKE | Strong ML tooling (Vertex) | Smaller OpenTofu community |
| Azure | NC series | Azure DB for PG | Azure Cache | ACI / AKS | Strong enterprise integration | Most complex IAM |
| Hetzner Cloud | Dedicated GPU servers | None (self-managed) | None | Docker + Compose | Lowest cost for GPU; simple | No managed PG/Redis; ops burden |
| DigitalOcean | GPU Droplets (limited) | Managed PG | Managed Redis | App Platform | Simple; good cost | Limited GPU selection |
| Fly.io | None | Managed PG (via add-on) | Upstash Redis | Fly machines | Very low ops overhead | No GPU; limited scale |

---

## Decision

**AWS as the primary cloud deployment target**, with **Hetzner Cloud as a cost-optimized alternative for GPU-heavy workloads** (LLM benchmarking, vLLM serving experiments).

### AWS Target Architecture

```
Internet
  ↓ HTTPS
  ALB (Application Load Balancer)
  ├── ECS Fargate — API Service (FastAPI)
  └── ECS Fargate — Worker Service (Celery)
        ├── RDS PostgreSQL (Multi-AZ for production)
        ├── ElastiCache Redis (cluster mode)
        └── EC2 G4dn / G5 instance — vLLM serving (ADR-013)

ECR — Container registry
Secrets Manager — JWT_SECRET_KEY, DB credentials, API keys
S3 — Model artifacts, evaluation results, backup storage
CloudWatch — Logs (forwarded from OTel Collector)
```

### Hetzner Use

Hetzner dedicated GPU servers (e.g., AX52 with RTX 3090, ~€130/month) are used for:
- LLM benchmarking during Phase 8/11 (significantly cheaper than AWS GPU instances)
- vLLM serving experiments when cost optimisation is the priority
- Local-equivalent reproducibility testing

Hetzner is **not** the production target; it lacks managed database and Redis services.

### IaC Separation

Separate OpenTofu root modules for AWS and Hetzner allow deploying to either provider independently. The application layer is provider-agnostic (containers + environment variables).

---

## Rationale

**Why AWS over GCP:**  
AWS has the largest OpenTofu/Terraform provider ecosystem and the most complete set of managed services aligned with this project's stack (RDS PostgreSQL + pgvector extension, ElastiCache, Secrets Manager, ECS Fargate). The GPU instance selection on EC2 (G4dn, G5, P3) is broader than GCP's equivalent.

**Why AWS over Azure:**  
Azure's IAM model (RBAC + Active Directory) adds operational complexity disproportionate to this project's scale. AWS IAM is better documented for container-based deployments in the OpenTofu community.

**Why not Hetzner as primary:**  
Hetzner does not offer managed PostgreSQL or Redis, shifting operational responsibility to self-managed database replication, backup, and Redis HA. The RPO < 1 hour / RTO < 4 hours recovery objectives (§19) are significantly harder to meet without managed services.

**Why not DigitalOcean / Fly.io:**  
Neither offers GPU instances suitable for vLLM serving. GPU inference is a first-class requirement for the LLM serving layer.

---

## Consequences

**Positive:**
- RDS PostgreSQL handles automated backups, Multi-AZ failover, and point-in-time recovery — directly addressing the RPO/RTO requirements (§19).
- ElastiCache Redis provides managed HA for the Celery broker without self-managed Redis replication.
- ECS Fargate eliminates EC2 instance management for the API and worker services.
- Secrets Manager integrates with IAM roles — no secret injection via environment files in production (SEC-004).
- Hetzner option preserves cost efficiency for GPU-intensive experiments without committing to expensive AWS GPU instances during development.

**Negative / Trade-offs:**
- AWS cost is higher than Hetzner or DigitalOcean at equivalent compute.
- ECS Fargate does not support GPU instances; the vLLM serving component requires an EC2 instance with GPU, adding operational complexity.
- AWS vendor-specific services (ECS, RDS, ElastiCache) create soft lock-in; mitigated by container portability and the dual AWS/Hetzner IaC structure.

**Risks and Mitigations:**
- Cost overrun during Phase 26 experiments: mitigated by using Hetzner for GPU workloads and AWS Free Tier / Spot instances for API/worker during initial testing.
- RDS PostgreSQL pgvector extension availability: confirmed supported on RDS PostgreSQL 15+ with the `pgvector` extension.
- ECS Fargate cold-start latency: mitigated by setting minimum running task count to 1 (no scale-to-zero in production).

---

## Review Triggers

Revisit this ADR if:
- GCP Vertex AI offers a significantly better managed LLM serving option that reduces operational overhead for ADR-013.
- AWS pricing changes make an alternative provider more cost-effective at the project's scale.
- A multi-cloud or hybrid requirement emerges (e.g., data residency constraints).
