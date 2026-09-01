# Data Card: Customers Dataset

**Dataset Name:** Acme Store Customers  
**Version:** 1.0  
**Creation Date:** 2026-01-01  
**Generator:** `scripts/generate_all_data.py` (seed=42)  
**Format:** CSV  
**Location:** `data/structured/customers/customers.csv`

---

## Summary

Synthetic dataset of 1,000 customer profiles for the Acme Store fictional e-commerce platform. All data is purely synthetic and generated with a fixed random seed for reproducibility.

---

## Dataset Statistics

| Attribute | Value |
|-----------|-------|
| Total records | 1,000 |
| File format | CSV (UTF-8, with header) |
| File size | ~120 KB |
| Unique customer IDs | 1,000 |
| Unique email addresses | 1,000 |

---

## Schema

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| customer_id | string | Unique identifier (CUS-XXXX) | PK, format CUS-0001 to CUS-1000 |
| first_name | string | Customer's first name | Not null |
| last_name | string | Customer's last name | Not null |
| email | string | Email address | Unique, not null |
| phone | string | Phone number | Format: (XXX) XXX-XXXX |
| address | string | Street address | Synthetic |
| city | string | City | US cities |
| state | string | State (2-letter code) | US states |
| zip_code | string | ZIP code | 5-digit format |
| customer_segment | string | Account tier | Enum: standard, premium, business, enterprise |
| account_status | string | Account status | Enum: active, inactive, suspended |
| created_date | date | Account creation date | Range: 2022-01-01 to 2025-12-31 |
| total_orders | integer | Lifetime order count | >= 0 |
| lifetime_value | float | Total spend in USD | >= 0.00 |

---

## Distribution

### Customer Segment
| Segment | Count | Percentage |
|---------|-------|------------|
| standard | ~650 | 65% |
| premium | ~200 | 20% |
| business | ~100 | 10% |
| enterprise | ~50 | 5% |

### Account Status
| Status | Count | Percentage |
|--------|-------|------------|
| active | ~870 | 87% |
| inactive | ~100 | 10% |
| suspended | ~30 | 3% |

---

## Data Quality Notes

- All names are generated from a synthetic name pool — any resemblance to real persons is coincidental.
- Email addresses use fictional domains (e.g., @example.com, @testmail.com).
- Phone numbers are in valid US format but are synthetic.
- Addresses use real US city/state/ZIP combinations for geographic realism.
- `lifetime_value` is consistent with `total_orders` (reasonable average order value per segment).

---

## Relationships

```
customers (customer_id)
    |-- orders.customer_id (FK)
    |-- support_tickets.customer_id (FK)
    |-- conversations.customer_id (FK)
```

---

## Intended Use

- Training and evaluating customer-facing AI support agents.
- Testing retrieval-augmented generation (RAG) pipelines with real customer context.
- Benchmarking customer segmentation and personalization models.

---

## Limitations

- Synthetic data does not capture real purchasing behavior patterns.
- `lifetime_value` is randomly generated within segment-appropriate ranges, not derived from order history.
- No demographic attributes (age, gender) are included by design.
