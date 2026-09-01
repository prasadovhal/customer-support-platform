-- =============================================================================
-- Acme Store — Seed Data
-- SYNTHETIC DATA — For development and AI/ML experimentation only
-- =============================================================================
--
-- USAGE:
--   1. Run generate_all_data.py to generate CSV files:
--        python scripts/generate_all_data.py --seed 42
--
--   2. Apply schema:
--        psql -d acmestore -f data/database/schema.sql
--
--   3. Load CSV data using COPY:
--        psql -d acmestore -c "\COPY customers FROM 'data/structured/customers/customers.csv' CSV HEADER"
--        psql -d acmestore -c "\COPY products FROM 'data/structured/products/products.csv' CSV HEADER"
--        psql -d acmestore -c "\COPY orders FROM 'data/structured/orders/orders.csv' CSV HEADER"
--        psql -d acmestore -c "\COPY support_tickets FROM 'data/structured/tickets/support_tickets.csv' CSV HEADER"
--
-- =============================================================================

-- Quick-start sample data for testing (5 customers, 5 products, 5 orders)
-- These are in addition to the generated CSV data.

INSERT INTO customers (customer_id, first_name, last_name, email, phone,
    customer_segment, account_status, country, state, city,
    registration_date, preferred_language, created_at, updated_at)
VALUES
    ('CUS-TEST1', 'Alice', 'TestUser', 'alice.test@syntheticmail.example', '+1-555-100-0001',
     'standard', 'active', 'US', 'CA', 'San Francisco',
     '2024-01-15', 'en', NOW(), NOW()),
    ('CUS-TEST2', 'Bob', 'TestUser', 'bob.test@syntheticmail.example', '+1-555-100-0002',
     'premium', 'active', 'US', 'NY', 'New York',
     '2023-06-01', 'en', NOW(), NOW()),
    ('CUS-TEST3', 'Carol', 'TestUser', 'carol.test@syntheticmail.example', '+1-555-100-0003',
     'enterprise', 'active', 'US', 'TX', 'Austin',
     '2022-03-10', 'en', NOW(), NOW()),
    ('CUS-TEST4', 'Dave', 'TestUser', 'dave.test@syntheticmail.example', '+1-555-100-0004',
     'business', 'active', 'US', 'WA', 'Seattle',
     '2024-09-20', 'en', NOW(), NOW()),
    ('CUS-TEST5', 'Eva', 'TestUser', 'eva.test@syntheticmail.example', '+1-555-100-0005',
     'standard', 'suspended', 'US', 'FL', 'Miami',
     '2023-11-05', 'es', NOW(), NOW())
ON CONFLICT (customer_id) DO NOTHING;

INSERT INTO products (product_id, sku, product_name, category, subcategory, description,
    price, currency, stock_status, warranty_months, return_window_days, is_active, created_at, updated_at)
VALUES
    ('PROD-T01', 'SKU-LAP-T001', 'AcmePro X1 Laptop (Test)', 'Laptops', 'Laptops',
     '14-inch test laptop, 16GB RAM, 512GB SSD', 999.99, 'USD', 'in_stock', 24, 15, TRUE, NOW(), NOW()),
    ('PROD-T02', 'SKU-PHN-T001', 'NovPhone 5 Pro (Test)', 'Smartphones', 'Smartphones',
     '5G test smartphone, 48MP camera', 699.99, 'USD', 'in_stock', 12, 15, TRUE, NOW(), NOW()),
    ('PROD-T03', 'SKU-ACC-T001', 'AcmeCase T1 (Test)', 'Accessories', 'Accessories',
     'Protective test case', 29.99, 'USD', 'in_stock', 6, 30, TRUE, NOW(), NOW()),
    ('PROD-T04', 'SKU-AUD-T001', 'NovaSound BT100 (Test)', 'Audio', 'Audio',
     'Test Bluetooth headphones with ANC', 149.99, 'USD', 'in_stock', 12, 30, TRUE, NOW(), NOW()),
    ('PROD-T05', 'SKU-LAP-T002', 'SwiftBook T1 Ultra (Test)', 'Laptops', 'Laptops',
     'Slim test ultrabook', 1299.99, 'USD', 'out_of_stock', 24, 15, TRUE, NOW(), NOW())
ON CONFLICT (product_id) DO NOTHING;

INSERT INTO orders (order_id, customer_id, order_date, product_id, quantity,
    unit_price, total_amount, currency, payment_method, payment_status,
    order_status, shipping_method, tracking_number, expected_delivery_date,
    actual_delivery_date, created_at, updated_at)
VALUES
    ('ORD-T0001', 'CUS-TEST1', '2025-11-01', 'PROD-T01', 1, 999.99, 999.99, 'USD',
     'credit_card', 'paid', 'delivered', 'standard', 'TRACK-TEST0001', '2025-11-08', '2025-11-07', NOW(), NOW()),
    ('ORD-T0002', 'CUS-TEST2', '2025-12-15', 'PROD-T02', 2, 699.99, 1399.98, 'USD',
     'paypal', 'paid', 'shipped', 'express', 'TRACK-TEST0002', '2025-12-18', NULL, NOW(), NOW()),
    ('ORD-T0003', 'CUS-TEST3', '2025-10-20', 'PROD-T04', 5, 149.99, 749.95, 'USD',
     'bank_transfer', 'paid', 'delivered', 'next_day', 'TRACK-TEST0003', '2025-10-21', '2025-10-21', NOW(), NOW()),
    ('ORD-T0004', 'CUS-TEST4', '2026-01-05', 'PROD-T03', 3, 29.99, 89.97, 'USD',
     'credit_card', 'pending', 'placed', 'standard', NULL, '2026-01-13', NULL, NOW(), NOW()),
    ('ORD-T0005', 'CUS-TEST1', '2025-09-10', 'PROD-T01', 1, 999.99, 999.99, 'USD',
     'debit_card', 'refunded', 'returned', 'express', 'TRACK-TEST0005', '2025-09-14', '2025-09-13', NOW(), NOW())
ON CONFLICT (order_id) DO NOTHING;
