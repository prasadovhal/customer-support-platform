# Data Validation Report — Acme Store

> Run `python scripts/validate_all.py` to update this report with live results.

Generation seed: **42**

---

## Dataset Counts

| Dataset | Expected | Status |
|---------|---------|--------|
| Knowledge articles | ~90 | `raw/knowledge_base/` (10 categories) |
| FAQ questions | ~300 | `processed/evaluation/faq_questions.jsonl` |
| Golden QA | 70 (hand-crafted) | `evaluation/golden_qa.jsonl` |
| Retrieval eval | ~100 | `evaluation/retrieval_eval.jsonl` |
| Agent eval | ~50 | `evaluation/agent_eval.jsonl` |
| Classification eval | ~200 | `evaluation/classification_eval.csv` |
| Customers | ~1,000 | `structured/customers/customers.csv` |
| Products | ~100 | `structured/products/products.csv` |
| Orders | ~5,000 | `structured/orders/orders.csv` |
| Support tickets | ~1,000 | `structured/tickets/support_tickets.csv` |
| Conversations | ~300 | `processed/conversations/conversations.jsonl` |

---

## Validation Checks

### Customers
- [ ] Row count >= 900
- [ ] customer_id uniqueness
- [ ] email uniqueness
- [ ] customer_segment in {standard, premium, business, enterprise}
- [ ] account_status in {active, inactive, suspended}
- [ ] No null first_name or email

### Products
- [ ] Row count >= 90
- [ ] product_id uniqueness
- [ ] SKU uniqueness
- [ ] price > 0
- [ ] stock_status valid values

### Orders
- [ ] Row count >= 4,500
- [ ] order_id uniqueness
- [ ] customer_id references valid customers
- [ ] product_id references valid products
- [ ] Delivered orders have actual_delivery_date
- [ ] Cancelled orders have no actual_delivery_date
- [ ] actual_delivery_date >= order_date

### Support Tickets
- [ ] Row count >= 900
- [ ] ticket_id uniqueness
- [ ] customer_id references valid customers
- [ ] order_id references valid orders (where not null)
- [ ] priority in {P0, P1, P2, P3}
- [ ] category in valid set
- [ ] satisfaction score only on resolved/closed

### Conversations
- [ ] Record count >= 250
- [ ] conversation_id uniqueness
- [ ] Required fields present
- [ ] resolution in {resolved, escalated, unresolved}
- [ ] messages is non-empty list
- [ ] customer_id references valid customers
- [ ] Intent distribution: no single intent exceeds 20% of total

### Knowledge Base
- [ ] Article count >= 15 (actual: 90)
- [ ] All articles have required YAML frontmatter
- [ ] document_id uniqueness
- [ ] Category values match known folders (10 categories including products and security)

### Golden QA
- [ ] Record count == 70
- [ ] All QA IDs unique (QA-0001 to QA-0070)
- [ ] All hand-crafted (no synthetic placeholder text)
- [ ] Difficulty distribution: easy/medium/hard/adversarial all present
- [ ] requires_tool entries have expected_tool field
- [ ] expected_document_ids reference valid KB document IDs

---

## Known Issues / Assumptions

1. Knowledge base expanded from ~20 to 90 articles across 10 categories (products and security added).
2. Golden QA dataset fully rebuilt: 70 hand-crafted pairs replacing previous 15 hand-crafted + 185 synthetic.
3. Conversation intent distribution corrected: was 76% check_return_policy (bug), now balanced across 13 intents (max ~16%).
4. Some ticket order_id references are empty (~30%) by design — not all support tickets are order-related.
5. Temporal policies (KB-RET-005) are included for the 2025 historical period to support temporal evaluation questions.
6. Data cards added for all 5 major datasets in `data/data_cards/`.
7. Schema documentation added for all tables in `data/schemas/`.

---

## How to Re-run Validation

```bash
python scripts/validate_all.py
```

Expected output: `Overall: ALL CHECKS PASSED`

---

## KB Category Coverage

| Category | Folder | Articles |
|----------|--------|---------|
| returns | returns/ | 10 |
| products | products/ | 12 |
| account | account/ | 10 |
| troubleshooting | troubleshooting/ | 10 |
| security | security/ | 10 |
| shipping | shipping/ | 8 |
| warranty | warranty/ | 8 |
| orders | orders/ | 8 |
| refunds | refunds/ | 7 |
| payments | payments/ | 7 |
| **Total** | | **90** |
