# Data Card: Support Tickets Dataset

**Dataset Name:** Acme Store Support Tickets  
**Version:** 1.0  
**Creation Date:** 2026-01-01  
**Generator:** `scripts/generate_all_data.py` (seed=42)  
**Format:** CSV  
**Location:** `data/structured/tickets/support_tickets.csv`

---

## Summary

Synthetic dataset of 1,000 customer support tickets with realistic categories, priorities, status progressions, and satisfaction scores. Designed to train and evaluate AI support triage and routing models.

---

## Dataset Statistics

| Attribute | Value |
|-----------|-------|
| Total records | 1,000 |
| File format | CSV (UTF-8, with header) |
| Unique ticket IDs | 1,000 |
| Tickets linked to orders | ~700 (70%) |
| Tickets without order reference | ~300 (30%) |
| Date range | 2024-01-01 to 2025-12-31 |

---

## Schema

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| ticket_id | string | Unique identifier (TKT-XXXX) | PK |
| customer_id | string | Reference to customers | FK -> customers.customer_id |
| order_id | string | Related order (optional) | FK -> orders.order_id, nullable |
| product_id | string | Related product (optional) | Nullable |
| subject | string | Brief ticket subject | Not null |
| description | string | Detailed issue description | Not null |
| category | string | Issue category | Enum (10 values) |
| priority | string | Priority level | Enum: P0, P1, P2, P3 |
| status | string | Current ticket status | Enum: open, in_progress, resolved, closed, escalated |
| created_date | datetime | Ticket creation timestamp | Not null |
| resolved_date | datetime | Resolution timestamp | Only for resolved/closed |
| resolution_notes | string | Agent's resolution summary | Nullable |
| satisfaction_score | integer | Customer satisfaction (1-5) | Only for resolved/closed; nullable |
| agent_id | string | Assigned agent | Nullable |

---

## Category Distribution

| Category | Approx. Count |
|----------|---------------|
| shipping | ~180 |
| returns | ~170 |
| refunds | ~150 |
| technical | ~130 |
| payments | ~110 |
| account | ~100 |
| orders | ~90 |
| warranty | ~50 |
| products | ~20 |

---

## Priority Distribution

| Priority | Description | Approx. Count |
|----------|-------------|---------------|
| P0 | Critical — immediate response | ~50 |
| P1 | High — 4-hour SLA | ~200 |
| P2 | Medium — 24-hour SLA | ~450 |
| P3 | Low — 72-hour SLA | ~300 |

---

## Business Rule Enforcement

- Satisfaction scores only appear on resolved or closed tickets.
- `resolved_date` is always after `created_date`.
- `order_id` references valid orders when present.
- ~70% of tickets that have an order reference use an order belonging to the same customer.

---

## Intended Use

- Training ticket classification models (category, priority prediction).
- Evaluating customer satisfaction prediction.
- Testing AI triage and routing for support escalation flows.

---

## Limitations

- Ticket text is template-based, not free-form; limited linguistic diversity.
- Satisfaction scores do not correlate with resolution quality in the synthetic data.
