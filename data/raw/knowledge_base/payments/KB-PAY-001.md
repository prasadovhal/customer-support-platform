---
document_id: KB-PAY-001
title: Supported Payment Methods
category: payments
subcategory: payment_methods
source: Acme Store Internal Knowledge Base
source_type: synthetic
source_url: null
license: internal
version: "2.0"
effective_from: "2026-01-01"
effective_to: null
product_scope: all
customer_segment: all
language: en
created_at: "2026-01-01T00:00:00Z"
updated_at: "2026-01-01T00:00:00Z"
---

# Supported Payment Methods

**Version 2.0 — Effective January 1, 2026**

## Overview

Acme Store supports multiple payment methods to accommodate different customer needs. This document lists all accepted payment methods and any conditions or restrictions.

## Accepted Payment Methods

### Credit and Debit Cards

Acme Store accepts major credit and debit cards:

- Visa
- Mastercard
- American Express
- Discover

Cards must be issued by a bank in a supported country. Prepaid cards are accepted but may not support refunds — a check or bank transfer may be issued instead for prepaid card refunds.

### PayPal

PayPal is accepted for all domestic and international orders. PayPal Express Checkout is available for faster checkout.

### Bank Transfer (ACH)

Direct bank transfer via ACH is available for:

- Business accounts
- Enterprise accounts
- Orders over $1,000

ACH transfers take 2–3 business days to clear. Orders are held until payment clears.

### Cryptocurrency

Select cryptocurrencies are accepted for domestic orders:

- Bitcoin (BTC)
- Ethereum (ETH)

Cryptocurrency payments are converted at the exchange rate at the time of transaction. Crypto payments are non-refundable in cryptocurrency — refunds for crypto-paid orders are issued as store credit or bank transfer.

### Invoice / Net-30 (Business and Enterprise)

Business and enterprise customers may apply for invoice billing with net-30 payment terms. This requires credit approval. Contact billing@acmestore.example to apply.

## Payment Security

All payment transactions are:

- Processed over TLS-encrypted connections
- PCI-DSS compliant
- Never stored in full on Acme Store's servers (tokenized)

## Currency

All prices are in USD. International customers may be charged in their local currency by their card issuer, with conversion at their bank's exchange rate.

## Split Payments

Acme Store does not currently support splitting a single order across multiple payment methods.

## Saving Payment Methods

You can save payment methods to your account for faster checkout. Saved cards are tokenized — Acme Store does not store full card numbers.
