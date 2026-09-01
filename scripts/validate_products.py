"""Validate products.csv"""
import csv
import os
import sys

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "structured", "products", "products.csv")

REQUIRED_FIELDS = ["product_id","sku","product_name","category","price",
                   "stock_status","warranty_months","return_window_days","is_active"]
VALID_STOCK = {"in_stock","out_of_stock","discontinued"}


def validate():
    passed = True
    path = os.path.abspath(DATA_FILE)
    if not os.path.exists(path):
        print(f"  [FAIL] File not found: {path}")
        return False

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"\n[Products] Loaded {len(rows)} rows from {path}")

    if len(rows) < 90:
        print(f"  [FAIL] Expected ~100 rows, got {len(rows)}")
        passed = False
    else:
        print(f"  [PASS] Row count: {len(rows)}")

    # Uniqueness
    ids = [r["product_id"] for r in rows]
    skus = [r["sku"] for r in rows]
    if len(ids) != len(set(ids)):
        print(f"  [FAIL] Duplicate product_ids")
        passed = False
    else:
        print(f"  [PASS] product_id uniqueness")

    if len(skus) != len(set(skus)):
        print(f"  [FAIL] Duplicate SKUs")
        passed = False
    else:
        print(f"  [PASS] SKU uniqueness")

    # Price validation
    bad_price = []
    for r in rows:
        try:
            p = float(r.get("price", 0))
            if p <= 0:
                bad_price.append(r["product_id"])
        except ValueError:
            bad_price.append(r["product_id"])
    if bad_price:
        print(f"  [FAIL] Invalid prices in {len(bad_price)} rows")
        passed = False
    else:
        print(f"  [PASS] Price validation")

    # Stock status
    bad_stock = [r["product_id"] for r in rows if r.get("stock_status") not in VALID_STOCK]
    if bad_stock:
        print(f"  [FAIL] Invalid stock_status in {len(bad_stock)} rows")
        passed = False
    else:
        print(f"  [PASS] stock_status values")

    # Category distribution
    cats = {}
    for r in rows:
        cats[r.get("category","unknown")] = cats.get(r.get("category","unknown"), 0) + 1
    print(f"  [INFO] Category distribution: {cats}")
    return passed


if __name__ == "__main__":
    sys.exit(0 if validate() else 1)
