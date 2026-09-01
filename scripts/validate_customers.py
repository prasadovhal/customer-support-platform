"""Validate customers.csv"""
import csv
import os
import sys

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "structured", "customers", "customers.csv")

REQUIRED_FIELDS = ["customer_id","first_name","last_name","email","phone",
                   "customer_segment","account_status","country","registration_date",
                   "preferred_language","created_at","updated_at"]
VALID_SEGMENTS = {"standard","premium","business","enterprise"}
VALID_STATUSES = {"active","inactive","suspended"}
VALID_LANGUAGES = {"en","es","fr","de","pt","zh","ja","ko","ar"}


def validate():
    passed = True
    path = os.path.abspath(DATA_FILE)
    if not os.path.exists(path):
        print(f"  [FAIL] File not found: {path}")
        return False

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"\n[Customers] Loaded {len(rows)} rows from {path}")

    # Count check
    if len(rows) < 900:
        print(f"  [FAIL] Expected ~1000 rows, got {len(rows)}")
        passed = False
    else:
        print(f"  [PASS] Row count: {len(rows)}")

    # Required fields
    missing_fields = [f for f in REQUIRED_FIELDS if f not in (reader.fieldnames or [])]
    if missing_fields:
        print(f"  [FAIL] Missing columns: {missing_fields}")
        passed = False
    else:
        print(f"  [PASS] All required columns present")

    # Uniqueness
    ids = [r["customer_id"] for r in rows]
    if len(ids) != len(set(ids)):
        print(f"  [FAIL] Duplicate customer_ids found")
        passed = False
    else:
        print(f"  [PASS] customer_id uniqueness")

    emails = [r["email"] for r in rows]
    if len(emails) != len(set(emails)):
        print(f"  [FAIL] Duplicate emails found")
        passed = False
    else:
        print(f"  [PASS] email uniqueness")

    # Domain checks
    bad_seg = [r["customer_id"] for r in rows if r.get("customer_segment") not in VALID_SEGMENTS]
    if bad_seg:
        print(f"  [FAIL] Invalid customer_segment in {len(bad_seg)} rows")
        passed = False
    else:
        print(f"  [PASS] customer_segment values")

    bad_status = [r["customer_id"] for r in rows if r.get("account_status") not in VALID_STATUSES]
    if bad_status:
        print(f"  [FAIL] Invalid account_status in {len(bad_status)} rows")
        passed = False
    else:
        print(f"  [PASS] account_status values")

    # Null checks
    null_issues = [r["customer_id"] for r in rows if not r.get("first_name") or not r.get("email")]
    if null_issues:
        print(f"  [FAIL] Null first_name or email in {len(null_issues)} rows")
        passed = False
    else:
        print(f"  [PASS] Null check on required fields")

    print(f"  [INFO] Segment distribution: " +
          str({seg: sum(1 for r in rows if r.get("customer_segment") == seg) for seg in VALID_SEGMENTS}))
    return passed


if __name__ == "__main__":
    sys.exit(0 if validate() else 1)
