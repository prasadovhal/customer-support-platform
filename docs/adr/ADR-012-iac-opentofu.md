# ADR-012 — Infrastructure as Code: OpenTofu

**Status:** Accepted  
**Date:** 2026-09-13  
**Deciders:** Engineering Lead  
**Supersedes:** —  
**Superseded by:** —

---

## Context

Phase 26 requires infrastructure-as-code for reproducible deployment of the platform to AWS (and optionally Hetzner, per ADR-011). The IaC tool must manage: VPC, subnets, security groups, ECS clusters and services, RDS PostgreSQL, ElastiCache Redis, ALB, ECR, Secrets Manager entries, IAM roles, S3 buckets, and optional EC2 GPU instances.

In August 2023 HashiCorp changed Terraform's license from MPL-2.0 to the Business Source License (BSL 1.1), which restricts use in competing products and services. The open-source fork, **OpenTofu**, was created under the Linux Foundation in response, maintaining MPL-2.0 licensing and full HCL compatibility with Terraform.

---

## Decision Drivers

| Driver | Weight | Notes |
|---|---|---|
| Open-source license (MPL-2.0) | High | Project principle: open-source/self-hostable tools |
| Terraform HCL compatibility | High | Existing community modules, examples, and knowledge transfer |
| Provider ecosystem | High | AWS and Hetzner providers must be available and stable |
| Active maintenance / CNCF backing | High | Long-term project viability |
| Learning value | Medium | IaC at Principal DS level requires industry-standard tooling |
| State management | Medium | Remote state in S3 + DynamoDB locking |

---

## Considered Options

| Option | License | HCL compat. | AWS provider | Hetzner provider | Learning curve | Notes |
|---|---|---|---|---|---|---|
| **OpenTofu** | MPL-2.0 | Full | Excellent | Yes | Low (same as Terraform) | CNCF project; BSL-free |
| Terraform (HashiCorp) | BSL 1.1 | N/A (source) | Excellent | Yes | Low | BSL restricts competing SaaS use |
| Pulumi | Apache 2.0 | No (Python/TS SDK) | Excellent | Yes | Medium | Different paradigm; Python SDK is compelling but adds context switch |
| AWS CDK | Apache 2.0 | No (Python/TS) | AWS-only | No | Medium | AWS-specific; no Hetzner support |
| Ansible | GPL-3.0 | No | Yes (modules) | Yes | Medium | Config management, not declarative IaC |
| Crossplane | Apache 2.0 | No (K8s CRDs) | Yes | Limited | High | Requires Kubernetes control plane |

---

## Decision

Use **OpenTofu** as the infrastructure-as-code tool.

### Repository Structure

```
infrastructure/
├── modules/
│   ├── networking/          # VPC, subnets, security groups
│   ├── compute/             # ECS cluster, services, task definitions
│   ├── database/            # RDS PostgreSQL
│   ├── cache/               # ElastiCache Redis
│   ├── storage/             # S3 buckets
│   ├── secrets/             # Secrets Manager entries
│   └── gpu-instance/        # EC2 GPU instance for vLLM
├── environments/
│   ├── dev/                 # Development environment
│   ├── staging/
│   └── production/
└── hetzner/                 # Hetzner GPU experiment environment
```

### State Management

Remote state in S3 bucket with DynamoDB table for state locking — standard pattern for team IaC workflows.

```hcl
terraform {
  backend "s3" {
    bucket         = "acme-support-tfstate"
    key            = "environments/production/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "acme-support-tfstate-lock"
    encrypt        = true
  }
}
```

### Version Pinning

```hcl
terraform {
  required_version = ">= 1.6.0"   # OpenTofu 1.6+ (equivalent to Terraform 1.6)
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.45"
    }
  }
}
```

---

## Rationale

**Why OpenTofu over Terraform:**  
The HashiCorp BSL 1.1 license introduces legal ambiguity for any project that could be considered a "competing product." While a customer support AI platform is unlikely to trigger this clause, the project principle of open-source/self-hostable tools applies to the development toolchain as well. OpenTofu is the CNCF-backed, MPL-2.0-licensed continuation of Terraform with 100% HCL compatibility — it provides all the benefits of Terraform without the license risk.

**Why OpenTofu over Pulumi:**  
Pulumi's Python SDK is genuinely appealing for a Python-heavy project. However, the Pulumi paradigm (imperative Python code managing declarative infrastructure) creates a context switch from the declarative HCL mental model. For IaC that will be reviewed, shared, and extended by engineers familiar with Terraform/OpenTofu (the dominant industry skill), HCL is the better choice. Pulumi is a Phase 22 experimentation candidate if the Python-native approach proves more maintainable.

**Why not AWS CDK:**  
CDK is AWS-specific. The dual AWS/Hetzner deployment strategy (ADR-011) requires a tool with providers for both. CDK has no Hetzner support.

**Why not Ansible:**  
Ansible is a configuration management tool, not a declarative infrastructure provisioning tool. It can complement OpenTofu (for post-provisioning configuration) but is not a substitute for it.

---

## Consequences

**Positive:**
- MPL-2.0 license: no restrictions on use, modification, or commercial deployment.
- Full HCL compatibility means the entire Terraform community module ecosystem (`terraform-aws-modules/*`) is usable directly.
- CNCF governance provides long-term project continuity.
- OpenTofu CLI is a drop-in replacement: the same HCL, same `tofu init / plan / apply` commands.
- Remote state in S3 + DynamoDB is the industry-standard pattern, well-documented and widely understood.

**Negative / Trade-offs:**
- OpenTofu lags Terraform by ~1 release cycle; very new Terraform provider features may not be available immediately. For AWS provider `~> 5.0` this is not a concern.
- HCL has a learning curve for engineers unfamiliar with declarative infrastructure; Python-fluent engineers may prefer Pulumi's SDK approach.

**Risks and Mitigations:**
- OpenTofu provider compatibility divergence: mitigated by pinning provider versions (`~> 5.0`) and testing before upgrading.
- State corruption: mitigated by S3 versioning on the state bucket and DynamoDB locking.

---

## Review Triggers

Revisit this ADR if:
- OpenTofu falls significantly behind Terraform in provider support for AWS services used in Phase 26.
- A team-wide shift to Pulumi or CDK is justified by Python-native IaC productivity gains.
- The Hetzner deployment path is dropped, reducing the multi-provider requirement that disfavors CDK.
