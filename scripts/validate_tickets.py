"""Validate support_tickets.csv"""
import csv
import os
import sys

TICKETS_FILE   = os.path.join(os.path.dirname(__file__), "..", "data", "structured", "tickets", "support_tickets.csv")
CUSTOMERS_FILE  = os.path.join(os.path.dirname(__file__), "..", "data", "structured", "customers", "customers.csv")
ORDERS_FILE     = os.path.join(os.path.dirname(__file__), "..", "data", "structured", "orders", "orders.csv")
PRODUCTS_FILE   = os.path.join(os.path.dirname(__file__), "..", "data", "structured", "products", "products.csv")

VALID_PRIORITIES = {"P0","P1","P2","P3"}
VALID_STATUSES   = {"open","in_progress","waiting_for_customer","resolved","closed"}
VALID_CHANNELS   = {"web","email","chat","phone"}
VALID_CATS       = {"shipping","returns","refunds","payments","orders","products","warranty","account","technical","security"}


def load_ids(path, field):
    if not os.path.exists(os.path.abspath(path)):
        return set()
    with open(os.path.abspath(path), encoding="utf-8") as f:
        return {r[field] for r in csv.DictReader(f)}


def validate():
    passed = True
    path = os.path.abspath(TICKETS_FILE)
    if not os.path.exists(path):
        print(f"  [FAIL] File not found: {path}")
        return False

    customer_ids = load_ids(CUSTOMERS_FILE, "customer_id")
    order_ids    = load_ids(ORDERS_FILE, "order_id")
    product_ids  = load_ids(PRODUCTS_FILE, "product_id")

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"\n[Support Tickets] Loaded {len(rows)} rows")

    if len(rows) < 900:
        print(f"  [FAIL] Expected ~1000 tickets, got {len(rows)}")
        passed = False
    else:
        print(f"  [PASS] Row count: {len(rows)}")

    # Uniqueness
    ids = [r["ticket_id"] for r in rows]
    if len(ids) != len(set(ids)):
        print(f"  [FAIL] Duplicate ticket_ids")
        passed = False
    else:
        print(f"  [PASS] ticket_id uniqueness")

    # Referential integrity
    bad_cust = [r["ticket_id"] for r in rows if r.get("customer_id") not in customer_ids]
    if bad_cust:
        print(f"  [FAIL] {len(bad_cust)} tickets reference invalid customer_ids")
        passed = False
    else:
        print(f"  [PASS] customer_id referential integrity")

    bad_order = [r["ticket_id"] for r in rows
                 if r.get("order_id") and r["order_id"] not in order_ids]
    if bad_order:
        print(f"  [FAIL] {len(bad_order)} tickets reference invalid order_ids")
        passed = False
    else:
        print(f"  [PASS] order_id referential integrity (when present)")

    # Domain checks
    bad_pri = [r["ticket_id"] for r in rows if r.get("priority") not in VALID_PRIORITIES]
    if bad_pri:
        print(f"  [FAIL] Invalid priority in {len(bad_pri)} rows")
        passed = False
    else:
        print(f"  [PASS] priority values")

    bad_cat = [r["ticket_id"] for r in rows if r.get("category") not in VALID_CATS]
    if bad_cat:
        print(f"  [FAIL] Invalid category in {len(bad_cat)} rows")
        passed = False
    else:
        print(f"  [PASS] category values")

    # Satisfaction only on resolved/closed
    bad_sat = [r["ticket_id"] for r in rows
               if r.get("customer_satisfaction") and r.get("status") not in ("resolved","closed")]
    if bad_sat:
        print(f"  [WARN] {len(bad_sat)} non-resolved tickets have customer_satisfaction score")

    # Distribution info
    pri_dist = {p: sum(1 for r in rows if r.get("priority") == p) for p in VALID_PRIORITIES}
    cat_dist = {c: sum(1 for r in rows if r.get("category") == c) for c in VALID_CATS}
    escalated = sum(1 for r in rows if r.get("escalated","false").lower() == "true")
    print(f"  [INFO] Priority distribution: {pri_dist}")
    print(f"  [INFO] Category distribution: {cat_dist}")
    print(f"  [INFO] Escalation rate: {escalated}/{len(rows)} ({escalated/len(rows)*100:.1f}%)")
    return passed


if __name__ == "__main__":
    sys.exit(0 if validate() else 1)
