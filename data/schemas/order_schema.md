# Schema: orders

**Table:** `orders`  
**Source File:** `data/structured/orders/orders.csv`  
**SQL Definition:** `data/database/schema.sql`

---

## Columns

| Column | SQL Type | Nullable | Default | Description |
|--------|----------|----------|---------|-------------|
| order_id | VARCHAR(20) | NOT NULL | — | Primary key. Format: ORD-XXXXX |
| customer_id | VARCHAR(20) | NOT NULL | — | FK -> customers.customer_id |
| product_id | VARCHAR(20) | NOT NULL | — | FK -> products.product_id |
| quantity | INTEGER | NOT NULL | 1 | Units ordered |
| unit_price | NUMERIC(10,2) | NOT NULL | — | Price per unit at time of order |
| total_amount | NUMERIC(12,2) | NOT NULL | — | quantity * unit_price |
| order_date | DATE | NOT NULL | — | Date the order was placed |
| order_status | VARCHAR(30) | NOT NULL | 'placed' | Current order lifecycle state |
| payment_status | VARCHAR(20) | NOT NULL | 'pending' | Payment state |
| shipping_address | VARCHAR(500) | NOT NULL | — | Full delivery address |
| estimated_delivery_date | DATE | NULL | — | Expected delivery date |
| actual_delivery_date | DATE | NULL | — | Actual delivery date (set when delivered) |
| carrier | VARCHAR(50) | NULL | — | Shipping carrier name |
| tracking_number | VARCHAR(100) | NULL | — | Carrier tracking ID |

---

## Constraints

```sql
PRIMARY KEY (order_id)
FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
FOREIGN KEY (product_id) REFERENCES products(product_id)
CHECK (quantity >= 1)
CHECK (unit_price > 0)
CHECK (total_amount > 0)
CHECK (order_status IN (
    'placed', 'confirmed', 'processing', 'shipped',
    'out_for_delivery', 'delivered', 'delayed',
    'cancelled', 'returned', 'refunded'
))
CHECK (payment_status IN ('pending', 'paid', 'refunded', 'failed'))
CHECK (actual_delivery_date IS NULL OR actual_delivery_date >= order_date)
CHECK (estimated_delivery_date IS NULL OR estimated_delivery_date >= order_date)
```

---

## Business Rules

| Rule | Description |
|------|-------------|
| Delivered orders | Must have `actual_delivery_date` set |
| Cancelled orders | Must NOT have `actual_delivery_date` |
| Refunded payment status | Only allowed for status `returned` or `refunded` |
| Tracking number | Required once order is `shipped` or later |

---

## Indexes

```sql
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_product_id ON orders(product_id);
CREATE INDEX idx_orders_status ON orders(order_status);
CREATE INDEX idx_orders_date ON orders(order_date);
```

---

## Relationships

```
orders.customer_id --> customers.customer_id
orders.product_id --> products.product_id
orders.order_id <-- support_tickets.order_id (optional FK)
```
