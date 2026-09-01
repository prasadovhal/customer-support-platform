# Data Card: Evaluation Datasets

**Dataset Name:** Acme Store Evaluation Suite  
**Version:** 1.0  
**Creation Date:** 2026-01-01  
**Generator:** `scripts/generate_all_data.py` (seed=42) + manual curation  
**Location:** `data/evaluation/`

---

## Overview

The evaluation suite contains five datasets for benchmarking AI/ML components of the customer support platform.

---

## Dataset 1: Golden QA Pairs (`golden_qa.jsonl`)

### Summary

70 hand-crafted question-answer pairs covering all major support scenarios. Each pair is annotated with expected document IDs, difficulty, intent, and required capabilities.

### Statistics

| Attribute | Value |
|-----------|-------|
| Total pairs | 70 |
| Hand-crafted | 70 (100%) |
| Synthetic placeholders | 0 |
| Categories | returns, shipping, refunds, payments, orders, warranty, account, troubleshooting, products, security |

### Difficulty Distribution

| Difficulty | Count |
|------------|-------|
| easy | 20 |
| medium | 25 |
| hard | 15 |
| adversarial | 10 |

### Scenario Types

| Type | Count |
|------|-------|
| Simple retrieval | 15 |
| Paraphrased/semantic | 10 |
| Multi-hop reasoning | 10 |
| Temporal policy | 5 |
| Tool-calling | 10 |
| Adversarial/jailbreak | 10 |
| Out-of-domain/unanswerable | 5 |
| Policy override attempt | 5 |

### Schema (per record)

| Field | Type | Description |
|-------|------|-------------|
| qa_id | string | Unique ID (QA-XXXX) |
| question | string | Customer question |
| expected_answer | string | Reference answer |
| acceptable_answers | list | Alternative acceptable answers |
| expected_document_ids | list | KB articles that should be retrieved |
| expected_sections | list | Specific sections in those articles |
| intent | string | Customer intent label |
| category | string | Topic category |
| difficulty | string | easy / medium / hard / adversarial |
| requires_retrieval | bool | Whether KB lookup is needed |
| requires_tool | bool | Whether tool call is needed |
| requires_human | bool | Whether human escalation is needed |
| ground_truth_action | string | Expected action (if any) |
| expected_tool | string | Tool name (if requires_tool) |
| expected_tool_arguments | object | Expected arguments for tool call |

---

## Dataset 2: Retrieval Evaluation (`retrieval_eval.jsonl`)

100 records for evaluating document retrieval precision and recall.

| Field | Description |
|-------|-------------|
| eval_id | Unique ID |
| query | Search query |
| relevant_document_ids | Gold-standard relevant documents |
| irrelevant_document_ids | Hard negatives |
| difficulty | easy / medium / hard |

---

## Dataset 3: Agent Evaluation (`agent_eval.jsonl`)

50 multi-turn scenarios for evaluating AI agent tool use and decision-making.

| Field | Description |
|-------|-------------|
| scenario_id | Unique ID |
| scenario_type | Category of scenario |
| conversation_turns | List of user/agent message pairs |
| expected_tools | Tools that should be called |
| expected_outcome | Final state or resolution |
| requires_human_approval | Whether human-in-the-loop is needed |

---

## Dataset 4: Classification Evaluation (`classification_eval.csv`)

200 records for evaluating intent classification models.

| Field | Description |
|-------|-------------|
| eval_id | Unique ID |
| text | Customer message |
| true_intent | Gold-standard intent label |
| true_category | Topic category |
| true_priority | Expected priority (P0-P3) |
| difficulty | easy / medium / hard |

---

## Dataset 5: FAQ Questions (`processed/evaluation/faq_questions.jsonl`)

300 frequently asked questions derived from the knowledge base, with expected answers.

| Field | Description |
|-------|-------------|
| faq_id | Unique ID |
| question | FAQ question |
| expected_answer | Reference answer |
| source_document_id | KB article source |
| category | Topic category |

---

## Intended Use

- Automated benchmarking of RAG, agent, and classification components.
- Regression testing after model updates.
- Comparison of different retrieval strategies (BM25 vs. dense vs. hybrid).

---

## Limitations

- Adversarial cases are limited to common attack patterns — novel attacks may not be represented.
- Tool-calling scenarios use a fixed tool schema; schema changes require evaluation updates.
- Agent evaluation turn depth is limited to 5 turns per scenario.
