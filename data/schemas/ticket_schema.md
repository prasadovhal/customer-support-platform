# Schema: support_tickets

**Table:** `support_tickets`  
**Source File:** `data/structured/tickets/support_tickets.csv`  
**SQL Definition:** `data/database/schema.sql`

---

## Columns

| Column | SQL Type | Nullable | Default | Description |
|--------|----------|----------|---------|-------------|
| ticket_id | VARCHAR(20) | NOT NULL | — | Primary key. Format: TKT-XXXX |
| customer_id | VARCHAR(20) | NOT NULL | — | FK -> customers.customer_id |
| order_id | VARCHAR(20) | NULL | — | FK -> orders.order_id (optional) |
| product_id | VARCHAR(20) | NULL | — | Related product ID (optional) |
| subject | VARCHAR(500) | NOT NULL | — | Brief ticket subject line |
| description | TEXT | NOT NULL | — | Full issue description |
| category | VARCHAR(50) | NOT NULL | — | Issue topic category |
| priority | CHAR(2) | NOT NULL | 'P2' | Priority level |
| status | VARCHAR(20) | NOT NULL | 'open' | Current ticket state |
| created_date | TIMESTAMP | NOT NULL | — | Ticket creation timestamp |
| resolved_date | TIMESTAMP | NULL | — | Resolution timestamp |
| resolution_notes | TEXT | NULL | — | Summary of resolution |
| satisfaction_score | SMALLINT | NULL | — | Customer satisfaction rating (1-5) |
| agent_id | VARCHAR(20) | NULL | — | Assigned support agent ID |

---

## Constraints

```sql
PRIMARY KEY (ticket_id)
FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
FOREIGN KEY (order_id) REFERENCES orders(order_id)  -- nullable FK
CHECK (priority IN ('P0', 'P1', 'P2', 'P3'))
CHECK (status IN ('open', 'in_progress', 'resolved', 'closed', 'escalated'))
CHECK (category IN (
    'shipping', 'returns', 'refunds', 'payments', 'products',
    'account', 'troubleshooting', 'orders', 'warranty', 'security', 'other'
))
CHECK (satisfaction_score IS NULL OR (satisfaction_score >= 1 AND satisfaction_score <= 5))
CHECK (resolved_date IS NULL OR resolved_date >= created_date)
```

---

## Business Rules

| Rule | Description |
|------|-------------|
| Satisfaction score | Only set when status is `resolved` or `closed` |
| Resolution notes | Expected to be populated for `resolved` and `closed` tickets |
| Order FK | ~30% of tickets have no order reference — valid for account or general inquiries |
| Priority P0 | Should be escalated immediately; rare (<5% of tickets) |

---

## Indexes

```sql
CREATE INDEX idx_tickets_customer_id ON support_tickets(customer_id);
CREATE INDEX idx_tickets_order_id ON support_tickets(order_id);
CREATE INDEX idx_tickets_status ON support_tickets(status);
CREATE INDEX idx_tickets_category ON support_tickets(category);
CREATE INDEX idx_tickets_priority ON support_tickets(priority);
```

---

## Relationships

```
support_tickets.customer_id --> customers.customer_id
support_tickets.order_id --> orders.order_id (optional)
```
