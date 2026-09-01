"""
Acme Store — Master Validation Script
Runs all validators and prints a summary report.
Usage: python scripts/validate_all.py
"""
import importlib
import os
import sys

VALIDATORS = [
    ("validate_customers",   "Customers"),
    ("validate_products",    "Products"),
    ("validate_orders",      "Orders"),
    ("validate_tickets",     "Support Tickets"),
    ("validate_conversations","Conversations"),
    ("validate_knowledge_base","Knowledge Base"),
]

def run_all():
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    results = []
    for module_name, label in VALIDATORS:
        try:
            mod = importlib.import_module(module_name)
            passed = mod.validate()
            results.append((label, passed, None))
        except Exception as e:
            results.append((label, False, str(e)))

    print("\n" + "=" * 60)
    print("  ACME STORE — DATA VALIDATION SUMMARY")
    print("=" * 60)
    all_passed = True
    for label, passed, err in results:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        suffix = f"  ERROR: {err}" if err else ""
        print(f"  {label:<25} {status}{suffix}")
    print("=" * 60)
    if all_passed:
        print("  Overall: ALL CHECKS PASSED")
    else:
        print("  Overall: SOME CHECKS FAILED — review output above")
    print("=" * 60 + "\n")
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(run_all())
