---
document_id: KB-SEC-005
title: Security Incident Reporting and Bug Bounty
category: security
source: Acme Store Security Team
source_type: synthetic
version: "1.0"
effective_from: "2026-01-01"
effective_to: null
product_scope: all
customer_segment: all
language: en
---

# Security Incident Reporting and Bug Bounty

## Overview

Acme Store welcomes responsible disclosure of security vulnerabilities. We take all reports seriously and commit to prompt investigation and remediation.

## How to Report a Security Vulnerability

### Responsible Disclosure Policy

If you discover a security vulnerability in Acme Store's platform:

1. **Do not** exploit the vulnerability or access data beyond what is needed to demonstrate the issue.
2. **Do not** publicly disclose the vulnerability before we have had a chance to address it.
3. Submit your report to: security@acmestore.com

### What to Include in Your Report

- Vulnerability type (e.g., XSS, SQL injection, authentication bypass).
- Steps to reproduce (be as detailed as possible).
- Affected URL or endpoint.
- Proof of concept (screenshots, request/response logs).
- Your assessment of the impact.

### Response Timeline

| Stage | Timeline |
|-------|---------|
| Initial acknowledgment | Within 24 hours |
| Triage and severity assessment | Within 72 hours |
| Fix target date communication | Within 7 days |
| Patch deployment | Varies by severity (Critical: 7 days, High: 30 days, Medium: 90 days) |
| Public disclosure (coordinated) | After patch deployment |

## Bug Bounty Program

Acme Store operates a bug bounty program through a third-party platform.

### In-Scope Assets

- acmestore.com (web application)
- api.acmestore.com (API)
- Acme Store mobile apps (iOS and Android)

### Out-of-Scope Assets

- Third-party services and integrations.
- Social media accounts.
- Physical security vulnerabilities.

### Reward Tiers

| Severity | Reward Range |
|----------|-------------|
| Critical (CVSS 9.0–10.0) | $5,000–$25,000 |
| High (CVSS 7.0–8.9) | $1,000–$4,999 |
| Medium (CVSS 4.0–6.9) | $200–$999 |
| Low (CVSS 0.1–3.9) | $50–$199 |

Duplicate reports or out-of-scope issues are not eligible for rewards.

## Reporting Account Compromise (Customers)

If your account has been compromised, see KB-SEC-003 for immediate response steps.

## Related Articles

- KB-SEC-001: Account Security
- KB-SEC-003: Unauthorized Access Response
