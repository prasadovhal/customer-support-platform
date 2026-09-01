# Data Card: Orders Dataset

**Dataset Name:** Acme Store Orders  
**Version:** 1.0  
**Creation Date:** 2026-01-01  
**Generator:** `scripts/generate_all_data.py` (seed=42)  
**Format:** CSV  
**Location:** `data/structured/orders/orders.csv`

---

## Summary

Synthetic dataset of 5,000 order records linked to customers and products. Includes realistic order lifecycle states, temporal consistency, and enforced referential integrity.

---

## Dataset Statistics

| Attribute | Value |
|-----------|-------|
| Total records | 5,000 |
| File format | CSV (UTF-8, with header) |
| Unique order IDs | 5,000 |
| Customers referenced | All 1,000 (with repetition) |
| Products referenced | All 100 (with repetition) |
| Date range | 2023-01-01 to 2025-12-31 |

---

## Schema

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| order_id | string | Unique identifier (ORD-XXXXX) | PK |
| customer_id | string | Reference to customers | FK -> customers.customer_id |
| product_id | string | Reference to products | FK -> products.product_id |
| quantity | integer | Units ordered | 1–10 |
| unit_price | float | Price per unit at order time | > 0 |
| total_amount | float | quantity * unit_price | > 0 |
| order_date | date | Date order was placed | Not null |
| order_status | string | Current order status | Enum (10 values) |
| payment_status | string | Payment state | Enum: pending, paid, refunded, failed |
| shipping_address | string | Delivery address | Not null |
| estimated_delivery_date | date | Expected delivery date | >= order_date |
| actual_delivery_date | date | Actual delivery date | Only when delivered |
| carrier | string | Shipping carrier | Enum: UPS, FedEx, USPS, DHL |
| tracking_number | string | Carrier tracking ID | Not null when shipped |

---

## Order Status Distribution

| Status | Count | Percentage |
|--------|-------|------------|
| delivered | ~3,000 | 60% |
| cancelled | ~750 | 15% |
| processing | ~500 | 10% |
| shipped | ~400 | 8% |
| returned | ~200 | 4% |
| other statuses | ~150 | 3% |

---

## Business Rule Enforcement

- **Delivered orders**: Always have `actual_delivery_date` set; it is >= `order_date`.
- **Cancelled orders**: Never have `actual_delivery_date`.
- **Refunded payment status**: Only on orders with status `returned` or `refunded`.
- **Temporal consistency**: `estimated_delivery_date` >= `order_date`; `actual_delivery_date` >= `order_date`.

---

## Referential Integrity

- 0 FK violations: all `customer_id` and `product_id` values reference existing records.

---

## Intended Use

- Training order management AI agents.
- Evaluating tool-calling capabilities (get_order_status, cancel_order, track_shipment).
- Testing temporal reasoning about order states.

---

## Limitations

- Order frequency per customer is randomly distributed, not based on realistic behavior patterns.
- Product mix per order does not reflect real category preferences.
- Addresses may not match customer's registered address (realistic for gift orders).
