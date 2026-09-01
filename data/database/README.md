# Database Setup — Acme Store

This directory contains the PostgreSQL schema and seed data for the Acme Store Enterprise Customer Support AI/ML Platform.

## Prerequisites

- PostgreSQL 14+
- Database named `acmestore` (or adjust commands below)

## Setup Steps

### 1. Create the database

```bash
createdb acmestore
```

### 2. Apply schema

```bash
psql -d acmestore -f data/database/schema.sql
```

### 3. Generate synthetic data

```bash
python scripts/generate_all_data.py --seed 42
```

### 4. Load CSV data

```bash
psql -d acmestore -c "\COPY customers FROM 'data/structured/customers/customers.csv' CSV HEADER"
psql -d acmestore -c "\COPY products FROM 'data/structured/products/products.csv' CSV HEADER"
psql -d acmestore -c "\COPY orders FROM 'data/structured/orders/orders.csv' CSV HEADER"
psql -d acmestore -c "\COPY support_tickets FROM 'data/structured/tickets/support_tickets.csv' CSV HEADER"
```

> On Windows, use absolute paths or run from the project root.

### 5. Load sample seed data (optional)

```bash
psql -d acmestore -f data/database/seed.sql
```

### 6. Load conversation data (via Python)

Conversations are stored in JSONL format and loaded via a Python script (to be implemented in app layer).

## Verify Data Load

```sql
SELECT 'customers' AS tbl, COUNT(*) FROM customers
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'support_tickets', COUNT(*) FROM support_tickets;
```

Expected row counts:
| Table | Expected |
|-------|---------|
| customers | ~1,000+ |
| products | ~100+ |
| orders | ~5,000+ |
| support_tickets | ~1,000+ |

## Notes

- All data is **synthetic** — no real personal information.
- Referential integrity is enforced via foreign keys.
- Vector database tables are intentionally excluded — they will be populated by the RAG ingestion pipeline.
