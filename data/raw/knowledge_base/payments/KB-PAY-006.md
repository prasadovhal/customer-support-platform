---
document_id: KB-PAY-006
title: Payment Security and Fraud Prevention
category: payments
source: Acme Store Policy Portal
source_type: synthetic
version: "1.0"
effective_from: "2026-01-01"
effective_to: null
product_scope: all
customer_segment: all
language: en
---

# Payment Security and Fraud Prevention

## Overview

Acme Store uses multiple layers of security to protect customer payment information and detect fraudulent transactions.

## Payment Data Security

- All payment transactions are processed using **TLS 1.3** encryption.
- Acme Store is **PCI DSS Level 1** compliant — the highest level of payment card security.
- Card numbers are **never stored** on Acme Store servers. Tokenization is used for recurring or saved card payments.
- CVV codes are never stored after transaction authorization.

## Fraud Detection

Our automated fraud detection system monitors for:

- Multiple failed payment attempts
- Orders shipped to addresses that differ from billing address
- Unusually large orders for new accounts
- Multiple orders with different payment methods in a short period

Suspected fraudulent orders are placed on hold pending verification.

## What Happens When Fraud Is Suspected

If your order is flagged:

1. You receive an email asking you to verify your identity.
2. Verification methods include: OTP to registered phone, photo ID upload, or a call from our security team.
3. Order is released within 2-4 hours of successful verification.
4. If verification fails or is not completed within 24 hours, the order is cancelled and refunded.

## Reporting Unauthorized Charges

If you see a charge from Acme Store that you did not authorize:

1. Contact us at fraud@acmestore.com immediately.
2. We will freeze your account to prevent further charges.
3. We investigate and respond within 2 business days.
4. Unauthorized charges are refunded in full.

You should also contact your bank to dispute the charge independently.

## Tips to Protect Your Payment Information

- Never share your password or payment details over email or phone.
- Use strong, unique passwords (see KB-SEC-006).
- Enable two-factor authentication (see KB-ACC-003).
- Check your order history regularly for unfamiliar transactions.
- Use a virtual credit card for one-time purchases.

## Related Articles

- KB-PAY-002: Failed Payments
- KB-SEC-001: Account Security Best Practices
- KB-SEC-002: Recognizing Phishing and Scams
