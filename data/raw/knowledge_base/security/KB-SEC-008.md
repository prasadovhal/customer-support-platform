---
document_id: KB-SEC-008
title: Payment Security and Fraud Prevention
category: security
source: Acme Store Security Team
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

This article covers how Acme Store protects your payment information and what to do if you detect fraudulent charges.

## Payment Security Standards

Acme Store is certified to **PCI DSS Level 1** — the highest standard for payment card security in the industry. This means:

- Card numbers are never stored on Acme Store servers.
- Payments are processed through tokenization.
- All payment data is encrypted using AES-256.
- All connections use TLS 1.3.

## How Tokenization Works

When you save a payment method, your actual card number is sent to our payment processor, which returns a **token** (a random string). This token is stored by Acme Store, not the actual card number. If our servers were ever breached, attackers would only find tokens — useless without the payment processor's decryption keys.

## Fraud Detection

Acme Store uses machine learning models to detect fraudulent transactions in real time. Suspicious patterns include:

- Orders from an IP address in a different country than the billing address.
- Multiple orders using different payment methods on a new account.
- Unusually large orders for account history.
- Orders to freight forwarding addresses.

## 3D Secure Authentication

For high-value or suspicious orders, Acme Store may trigger 3D Secure (3DS) — an extra authentication step through your bank. You receive a one-time code from your bank to confirm the transaction.

## Unauthorized Charge Response

If you see an unauthorized charge from Acme Store:

1. Contact us at fraud@acmestore.com immediately.
2. Provide: the charge amount, date, and last 4 digits of the card.
3. We investigate and respond within 2 business days.
4. If confirmed fraudulent, we refund the charge and initiate an internal security review.

Simultaneously, contact your bank to dispute the charge via their standard chargeback process.

## Safe Shopping Practices

- Always check that the URL is **https://acmestore.com** (look for the lock icon).
- Avoid saving payment methods on shared or public computers.
- Use virtual card numbers for one-time purchases (many banks offer this feature).
- Monitor your bank statements regularly.

## Related Articles

- KB-PAY-002: Failed Payments
- KB-PAY-006: Payment Security (general)
- KB-SEC-002: Phishing and Scams
