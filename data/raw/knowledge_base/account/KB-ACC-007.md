---
document_id: KB-ACC-007
title: Managing Saved Payment Methods
category: account
source: Acme Store Policy Portal
source_type: synthetic
version: "1.0"
effective_from: "2026-01-01"
effective_to: null
product_scope: all
customer_segment: all
language: en
---

# Managing Saved Payment Methods

## Overview

Acme Store allows you to save multiple payment methods for faster checkout. This article explains how to add, update, and remove saved payment methods.

## Adding a Payment Method

1. Go to **Account** > **Payment Methods** > **Add Payment Method**.
2. Select the type: Credit/Debit Card, PayPal, or Bank Account.
3. Enter the required details.
4. Click **Save**.

For credit/debit cards, only the last 4 digits and card type are displayed after saving. Full card numbers are never stored by Acme Store (see KB-PAY-006).

## Setting a Default Payment Method

1. Go to **Account** > **Payment Methods**.
2. Find the payment method you want to set as default.
3. Click **Set as Default**.

The default payment method is used automatically at checkout unless you choose otherwise.

## Updating an Expiring Card

When a saved card is nearing its expiration date, you receive a reminder email 30 days in advance.

To update:

1. Go to **Account** > **Payment Methods**.
2. Click **Update** next to the card.
3. Enter the new expiration date and CVV.
4. Click **Save Changes**.

Note: Most major card networks support automatic card updates — your saved card may update automatically when reissued.

## Removing a Payment Method

1. Go to **Account** > **Payment Methods**.
2. Click **Remove** next to the payment method.
3. Confirm the removal.

You cannot remove a payment method if it is the only one on file and you have outstanding balances or active subscriptions.

## Payment Method Security

- Saved payment methods are tokenized — Acme Store stores a secure token, not the actual card number.
- Adding a new card requires CVV verification.
- Changes to saved payment methods may trigger a 2FA verification (see KB-ACC-003).
- You can view all recent charges associated with each payment method in **Account** > **Payment History**.

## Related Articles

- KB-PAY-001: Payment Methods Overview
- KB-PAY-006: Payment Security
- KB-ACC-003: Two-Factor Authentication
