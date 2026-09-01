"""Validate conversations.jsonl"""
import json
import os
import sys

CONV_FILE      = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "conversations", "conversations.jsonl")
CUSTOMERS_FILE  = os.path.join(os.path.dirname(__file__), "..", "data", "structured", "customers", "customers.csv")

REQUIRED_FIELDS = ["conversation_id","customer_id","channel","started_at","messages","primary_intent","resolution"]
VALID_RESOLUTION = {"resolved","escalated","unresolved"}
VALID_CHANNELS   = {"web","email","chat","phone"}


def load_customer_ids(path):
    import csv
    if not os.path.exists(os.path.abspath(path)):
        return set()
    with open(os.path.abspath(path), encoding="utf-8") as f:
        return {r["customer_id"] for r in csv.DictReader(f)}


def validate():
    passed = True
    path = os.path.abspath(CONV_FILE)
    if not os.path.exists(path):
        print(f"  [FAIL] File not found: {path}")
        return False

    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    print(f"\n[Conversations] Loaded {len(rows)} records")

    if len(rows) < 250:
        print(f"  [FAIL] Expected ~300 conversations, got {len(rows)}")
        passed = False
    else:
        print(f"  [PASS] Record count: {len(rows)}")

    # Uniqueness
    ids = [r.get("conversation_id") for r in rows]
    if len(ids) != len(set(ids)):
        print(f"  [FAIL] Duplicate conversation_ids")
        passed = False
    else:
        print(f"  [PASS] conversation_id uniqueness")

    # Required fields
    missing = [r.get("conversation_id","?") for r in rows
               if any(f not in r for f in REQUIRED_FIELDS)]
    if missing:
        print(f"  [FAIL] {len(missing)} records missing required fields")
        passed = False
    else:
        print(f"  [PASS] Required fields present")

    # Resolution values
    bad_res = [r.get("conversation_id","?") for r in rows
               if r.get("resolution") not in VALID_RESOLUTION]
    if bad_res:
        print(f"  [FAIL] Invalid resolution in {len(bad_res)} records")
        passed = False
    else:
        print(f"  [PASS] resolution values")

    # Messages structure
    bad_msgs = [r.get("conversation_id","?") for r in rows
                if not isinstance(r.get("messages"), list) or len(r.get("messages",[])) == 0]
    if bad_msgs:
        print(f"  [FAIL] {len(bad_msgs)} conversations have empty/invalid messages")
        passed = False
    else:
        print(f"  [PASS] messages structure")

    # Referential integrity (customer_id)
    customer_ids = load_customer_ids(CUSTOMERS_FILE)
    if customer_ids:
        bad_cust = [r.get("conversation_id","?") for r in rows
                    if r.get("customer_id") not in customer_ids]
        if bad_cust:
            print(f"  [FAIL] {len(bad_cust)} conversations reference invalid customer_ids")
            passed = False
        else:
            print(f"  [PASS] customer_id referential integrity")

    # Distribution
    res_dist = {r: sum(1 for c in rows if c.get("resolution") == r) for r in VALID_RESOLUTION}
    print(f"  [INFO] Resolution distribution: {res_dist}")
    escalated = sum(1 for r in rows if r.get("escalated") is True)
    print(f"  [INFO] Escalation rate: {escalated}/{len(rows)} ({escalated/len(rows)*100:.1f}%)")
    return passed


if __name__ == "__main__":
    sys.exit(0 if validate() else 1)
