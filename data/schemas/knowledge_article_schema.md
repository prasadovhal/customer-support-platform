# Schema: Knowledge Base Articles

**Format:** Markdown files with YAML frontmatter  
**Location:** `data/raw/knowledge_base/{category}/{document_id}.md`  
**Validator:** `scripts/validate_knowledge_base.py`

---

## File Naming Convention

```
{CATEGORY_CODE}-{SUBCATEGORY_CODE}-{NUMBER}.md
```

Examples:
- `KB-RET-001.md` — Returns category, article 001
- `KB-SHP-005.md` — Shipping category, article 005
- `KB-SEC-003.md` — Security category, article 003

---

## YAML Frontmatter Schema

All articles must begin with a YAML frontmatter block delimited by `---`:

```yaml
---
document_id: KB-RET-001
title: Standard Return Policy
category: returns
source: Acme Store Policy Portal
source_type: synthetic
version: "2.0"
effective_from: "2026-01-01"
effective_to: null
product_scope: all
customer_segment: all
language: en
---
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| document_id | string | YES | Unique ID matching filename (e.g., KB-RET-001) |
| title | string | YES | Human-readable article title |
| category | string | YES | One of 10 known categories (see below) |
| source | string | YES | Authoring department or system |
| source_type | string | YES | Always "synthetic" in this dataset |
| version | string | YES | Semantic version (e.g., "1.0", "2.0") |
| effective_from | date string | YES | ISO 8601 date when this version became active |
| effective_to | date string / null | YES | ISO 8601 date when this version expired; null = currently active |
| product_scope | string | YES | Product categories this applies to ("all" or comma-separated) |
| customer_segment | string | YES | Customer tiers this applies to ("all" or comma-separated) |
| language | string | YES | ISO 639-1 language code (e.g., "en") |

---

## Known Categories

```
shipping, returns, refunds, payments, products,
account, troubleshooting, orders, warranty, security
```

---

## Document ID Prefixes by Category

| Category | Prefix | Example |
|----------|--------|---------|
| returns | KB-RET | KB-RET-001 |
| shipping | KB-SHP | KB-SHP-001 |
| refunds | KB-REF | KB-REF-001 |
| payments | KB-PAY | KB-PAY-001 |
| orders | KB-ORD | KB-ORD-001 |
| warranty | KB-WAR | KB-WAR-001 |
| account | KB-ACC | KB-ACC-001 |
| troubleshooting | KB-TRB | KB-TRB-001 |
| products | KB-PRD | KB-PRD-001 |
| security | KB-SEC | KB-SEC-001 |

---

## Markdown Body Guidelines

After the frontmatter block, articles follow this structure:

```markdown
# Article Title

## Overview
Brief summary paragraph.

## Section Heading
Content...

## Related Articles
- KB-XXX-NNN: Title
```

Articles should include cross-references to related articles using their document IDs.

---

## Validation Rules (from validate_knowledge_base.py)

- All 8 required frontmatter fields must be present.
- `document_id` must be unique across all articles.
- `category` must be one of the 10 known categories.
- Minimum 15 articles required; target is ~100.
- `document_id` must match the filename (without extension).

---

## Temporal Policy Articles

Articles with `effective_to` set to a past date are "historical" policy documents:

- `KB-RET-005`: v1.0 policy, effective 2025-01-01 to 2025-12-31.
- These exist specifically to support temporal evaluation questions.
- RAG pipelines should surface these when queried about past time periods.
