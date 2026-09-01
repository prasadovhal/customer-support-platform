# Schema: customers

**Table:** `customers`  
**Source File:** `data/structured/customers/customers.csv`  
**SQL Definition:** `data/database/schema.sql`

---

## Columns

| Column | SQL Type | Nullable | Default | Description |
|--------|----------|----------|---------|-------------|
| customer_id | VARCHAR(20) | NOT NULL | — | Primary key. Format: CUS-XXXX (e.g., CUS-0001) |
| first_name | VARCHAR(100) | NOT NULL | — | Customer's given name |
| last_name | VARCHAR(100) | NOT NULL | — | Customer's family name |
| email | VARCHAR(255) | NOT NULL | — | Email address. Unique constraint. |
| phone | VARCHAR(20) | NULL | — | Phone number. Format: (XXX) XXX-XXXX |
| address | VARCHAR(500) | NULL | — | Street address (line 1 + line 2 combined) |
| city | VARCHAR(100) | NULL | — | City name |
| state | CHAR(2) | NULL | — | US state code (e.g., CA, NY) |
| zip_code | VARCHAR(10) | NULL | — | ZIP or postal code |
| customer_segment | VARCHAR(20) | NOT NULL | 'standard' | Account tier |
| account_status | VARCHAR(20) | NOT NULL | 'active' | Account lifecycle state |
| created_date | DATE | NOT NULL | — | Date account was created |
| total_orders | INTEGER | NOT NULL | 0 | Denormalized count of orders placed |
| lifetime_value | NUMERIC(12,2) | NOT NULL | 0.00 | Denormalized total spend in USD |

---

## Constraints

```sql
PRIMARY KEY (customer_id)
UNIQUE (email)
CHECK (customer_segment IN ('standard', 'premium', 'business', 'enterprise'))
CHECK (account_status IN ('active', 'inactive', 'suspended'))
CHECK (total_orders >= 0)
CHECK (lifetime_value >= 0)
```

---

## Indexes

```sql
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_segment ON customers(customer_segment);
CREATE INDEX idx_customers_status ON customers(account_status);
```

---

## Relationships

```
customers.customer_id <-- orders.customer_id (one-to-many)
customers.customer_id <-- support_tickets.customer_id (one-to-many)
customers.customer_id <-- conversations.customer_id (one-to-many)
```

---

## Sample Record

```csv
customer_id,first_name,last_name,email,phone,address,city,state,zip_code,customer_segment,account_status,created_date,total_orders,lifetime_value
CUS-0001,Alice,Johnson,alice.johnson@example.com,(415) 555-0123,123 Main St,San Francisco,CA,94105,premium,active,2023-03-15,12,2847.50
```

---

## Notes

- `total_orders` and `lifetime_value` are denormalized summary fields. They are set at generation time and may not exactly match derived counts from the orders table.
- `customer_id` format is zero-padded to 4 digits: CUS-0001 to CUS-1000.
