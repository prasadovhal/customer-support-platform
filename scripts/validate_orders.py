"""Validate orders.csv — referential integrity, business rules, temporal consistency."""
import csv
import os
import sys
from datetime import datetime

ORDERS_FILE   = os.path.join(os.path.dirname(__file__), "..", "data", "structured", "orders", "orders.csv")
CUSTOMERS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "structured", "customers", "customers.csv")
PRODUCTS_FILE  = os.path.join(os.path.dirname(__file__), "..", "data", "structured", "products", "products.csv")

VALID_STATUSES  = {"placed","confirmed","processing","shipped","out_for_delivery","delivered","delayed","cancelled","returned","refunded"}
VALID_PAY_STAT  = {"pending","paid","failed","refunded","partially_refunded"}
VALID_SHIP      = {"standard","express","next_day","international"}


def load_ids(path, field):
    with open(path, encoding="utf-8") as f:
        return {r[field] for r in csv.DictReader(f)}


def validate():
    passed = True
    for p in [ORDERS_FILE, CUSTOMERS_FILE, PRODUCTS_FILE]:
        if not os.path.exists(os.path.abspath(p)):
            print(f"  [FAIL] File not found: {p}")
            return False

    customer_ids = load_ids(os.path.abspath(CUSTOMERS_FILE), "customer_id")
    product_ids  = load_ids(os.path.abspath(PRODUCTS_FILE),  "product_id")

    with open(os.path.abspath(ORDERS_FILE), encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"\n[Orders] Loaded {len(rows)} rows")

    if len(rows) < 4500:
        print(f"  [FAIL] Expected ~5000 orders, got {len(rows)}")
        passed = False
    else:
        print(f"  [PASS] Row count: {len(rows)}")

    # Uniqueness
    ids = [r["order_id"] for r in rows]
    if len(ids) != len(set(ids)):
        print(f"  [FAIL] Duplicate order_ids")
        passed = False
    else:
        print(f"  [PASS] order_id uniqueness")

    # Referential integrity
    bad_cust = [r["order_id"] for r in rows if r.get("customer_id") not in customer_ids]
    if bad_cust:
        print(f"  [FAIL] {len(bad_cust)} orders reference non-existent customer_ids")
        passed = False
    else:
        print(f"  [PASS] customer_id referential integrity")

    bad_prod = [r["order_id"] for r in rows if r.get("product_id") not in product_ids]
    if bad_prod:
        print(f"  [FAIL] {len(bad_prod)} orders reference non-existent product_ids")
        passed = False
    else:
        print(f"  [PASS] product_id referential integrity")

    # Status validity
    bad_status = [r["order_id"] for r in rows if r.get("order_status") not in VALID_STATUSES]
    if bad_status:
        print(f"  [FAIL] Invalid order_status in {len(bad_status)} rows")
        passed = False
    else:
        print(f"  [PASS] order_status values")

    # Business rules
    delivered_no_date = [
        r["order_id"] for r in rows
        if r.get("order_status") == "delivered" and not r.get("actual_delivery_date")
    ]
    if delivered_no_date:
        print(f"  [FAIL] {len(delivered_no_date)} delivered orders missing actual_delivery_date")
        passed = False
    else:
        print(f"  [PASS] Delivered orders have actual_delivery_date")

    cancelled_with_date = [
        r["order_id"] for r in rows
        if r.get("order_status") == "cancelled" and r.get("actual_delivery_date")
    ]
    if cancelled_with_date:
        print(f"  [WARN] {len(cancelled_with_date)} cancelled orders have an actual_delivery_date (review)")
    else:
        print(f"  [PASS] Cancelled orders lack actual_delivery_date")

    # Temporal: delivery >= order date
    temporal_fail = 0
    for r in rows:
        if r.get("actual_delivery_date") and r.get("order_date"):
            try:
                od = datetime.strptime(r["order_date"], "%Y-%m-%d")
                dd = datetime.strptime(r["actual_delivery_date"], "%Y-%m-%d")
                if dd < od:
                    temporal_fail += 1
            except ValueError:
                pass
    if temporal_fail:
        print(f"  [FAIL] {temporal_fail} orders have delivery_date before order_date")
        passed = False
    else:
        print(f"  [PASS] Temporal consistency (delivery >= order date)")

    # Status distribution
    status_dist = {}
    for r in rows:
        s = r.get("order_status","unknown")
        status_dist[s] = status_dist.get(s, 0) + 1
    print(f"  [INFO] Order status distribution: {status_dist}")
    return passed


if __name__ == "__main__":
    sys.exit(0 if validate() else 1)
