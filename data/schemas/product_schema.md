# Schema: products

**Table:** `products`  
**Source File:** `data/structured/products/products.csv`  
**SQL Definition:** `data/database/schema.sql`

---

## Columns

| Column | SQL Type | Nullable | Default | Description |
|--------|----------|----------|---------|-------------|
| product_id | VARCHAR(20) | NOT NULL | — | Primary key. Format: PROD-XXX (e.g., PROD-001) |
| sku | VARCHAR(50) | NOT NULL | — | Stock Keeping Unit. Unique. |
| name | VARCHAR(255) | NOT NULL | — | Product display name |
| description | TEXT | NULL | — | Full product description |
| category | VARCHAR(50) | NOT NULL | — | Product category |
| sub_category | VARCHAR(50) | NULL | — | Product sub-category |
| brand | VARCHAR(100) | NULL | — | Manufacturer or brand name |
| price | NUMERIC(10,2) | NOT NULL | — | Current retail price in USD |
| cost | NUMERIC(10,2) | NULL | — | Internal cost price (not exposed to customers) |
| stock_quantity | INTEGER | NOT NULL | 0 | Current units in stock |
| stock_status | VARCHAR(20) | NOT NULL | 'in_stock' | Availability status |
| weight_kg | NUMERIC(8,3) | NULL | — | Product weight in kilograms |
| warranty_months | INTEGER | NULL | 12 | Standard warranty duration in months |
| is_returnable | BOOLEAN | NOT NULL | TRUE | Whether product can be returned |

---

## Constraints

```sql
PRIMARY KEY (product_id)
UNIQUE (sku)
CHECK (price > 0)
CHECK (stock_quantity >= 0)
CHECK (stock_status IN ('in_stock', 'low_stock', 'out_of_stock', 'discontinued'))
CHECK (warranty_months >= 0)
```

---

## Indexes

```sql
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_stock_status ON products(stock_status);
CREATE INDEX idx_products_sku ON products(sku);
```

---

## Category Values

Known category values: `laptops`, `smartphones`, `tablets`, `audio`, `wearables`, `networking`, `home_appliances`, `gaming`, `accessories`, `refurbished`

---

## Relationships

```
products.product_id <-- orders.product_id (one-to-many)
products.product_id <-- support_tickets.product_id (optional, one-to-many)
```

---

## Sample Record

```csv
product_id,sku,name,description,category,sub_category,brand,price,cost,stock_quantity,stock_status,weight_kg,warranty_months,is_returnable
PROD-001,ACM-LPT-001,AcmePro Laptop 15,15-inch productivity laptop with Intel Core i7,laptops,ultrabook,AcmeTech,1299.99,750.00,45,in_stock,1.850,12,true
```
