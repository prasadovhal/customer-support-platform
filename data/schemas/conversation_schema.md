# Schema: conversations (JSONL)

**Collection:** `conversations`  
**Source File:** `data/processed/conversations/conversations.jsonl`  
**Format:** JSONL (one JSON object per line)

---

## Top-Level Fields

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| conversation_id | string | NOT NULL | Unique ID. Format: CONV-XXXX |
| customer_id | string | NOT NULL | FK -> customers.customer_id |
| order_id | string | NULL | Related order (optional) |
| channel | string | NOT NULL | Contact channel |
| started_at | string (ISO 8601) | NOT NULL | Conversation start timestamp |
| ended_at | string (ISO 8601) | NULL | Conversation end timestamp |
| duration_seconds | integer | NULL | Total conversation duration |
| intent | string | NOT NULL | Primary customer intent |
| resolution | string | NOT NULL | Outcome of the conversation |
| satisfaction_score | integer | NULL | CSAT score (1-5) |
| messages | array | NOT NULL | Ordered list of conversation turns |
| metadata | object | NULL | Additional context fields |

---

## Message Object Schema

Each item in the `messages` array:

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| turn | integer | NOT NULL | Turn number (1-indexed) |
| role | string | NOT NULL | Enum: customer, agent, system |
| content | string | NOT NULL | Message text |
| timestamp | string (ISO 8601) | NOT NULL | Message timestamp |
| intent | string | NULL | Intent label for this turn (customer turns) |
| sentiment | string | NULL | Sentiment: positive, neutral, negative |

---

## Enum Values

### channel
`chat`, `email`, `phone`, `in-app`

### intent
`check_order_status`, `track_shipment`, `initiate_return`, `check_return_policy`, `check_return_eligibility`, `request_refund`, `check_refund_status`, `report_damaged_item`, `report_delayed_delivery`, `report_lost_package`, `password_reset`, `payment_failure`, `connectivity_problem`, `policy_exception_request`, `policy_override_attempt`, `escalation_request`, `tool_dependent`, `product_recommendation`, `warranty_claim`, `cancel_order`, `modify_order`, `check_shipping_options`, `check_shipping_time`, `account_security_changes`

### resolution
`resolved`, `escalated`, `unresolved`

---

## Conversation Intent Distribution

Based on generation with seed=42 (300 conversations):

| Intent | Count | Percentage |
|--------|-------|------------|
| initiate_return | ~49 | 16% |
| policy_exception_request | ~27 | 9% |
| policy_override_attempt | ~27 | 9% |
| check_refund_status | ~24 | 8% |
| payment_failure | ~23 | 8% |
| report_damaged_item | ~22 | 7% |
| escalation_request | ~22 | 7% |
| check_order_status | ~19 | 6% |
| track_shipment | ~18 | 6% |
| connectivity_problem | ~21 | 7% |
| check_return_policy | ~15 | 5% |
| Other intents | ~35 | 12% |

---

## Sample Record (Abbreviated)

```json
{
  "conversation_id": "CONV-0001",
  "customer_id": "CUS-0123",
  "order_id": "ORD-01234",
  "channel": "chat",
  "started_at": "2025-03-15T10:23:00Z",
  "ended_at": "2025-03-15T10:31:00Z",
  "duration_seconds": 480,
  "intent": "initiate_return",
  "resolution": "resolved",
  "satisfaction_score": 4,
  "messages": [
    {
      "turn": 1,
      "role": "customer",
      "content": "I'd like to return my laptop.",
      "timestamp": "2025-03-15T10:23:00Z",
      "intent": "initiate_return",
      "sentiment": "neutral"
    },
    {
      "turn": 2,
      "role": "agent",
      "content": "I'd be happy to help with that. Can you share your order number?",
      "timestamp": "2025-03-15T10:23:30Z",
      "intent": null,
      "sentiment": "positive"
    }
  ]
}
```
