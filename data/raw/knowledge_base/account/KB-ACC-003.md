---
document_id: KB-ACC-003
title: Two-Factor Authentication (2FA)
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

# Two-Factor Authentication (2FA)

## Overview

Two-factor authentication adds an extra layer of security to your Acme Store account by requiring a second verification step in addition to your password.

## Enabling 2FA

1. Log in to your account.
2. Go to **Account** > **Security** > **Two-Factor Authentication**.
3. Select your preferred 2FA method.
4. Follow the setup instructions for your chosen method.
5. Save the backup codes provided — these are for account recovery.

## Available 2FA Methods

### 1. Authenticator App (Recommended)

Use apps like Google Authenticator, Authy, or Microsoft Authenticator:

- Scan the QR code shown in settings.
- The app generates a 6-digit code every 30 seconds.
- Enter the code when prompted at login.

**Advantages**: Works without mobile signal, most secure.

### 2. SMS One-Time Password

A 6-digit code is sent to your verified phone number:

- Enter the code within 5 minutes of receipt.
- Rate limited: maximum 5 SMS codes per hour.

**Advantages**: Easy to use; **Disadvantages**: Vulnerable to SIM-swapping attacks.

### 3. Email OTP

A 6-digit code is sent to your registered email:

- Enter the code within 15 minutes.
- Less secure than authenticator app.

## What Triggers 2FA

2FA is required when:

- Logging in from a new device or browser.
- Logging in from a new geographic location.
- Changing sensitive account settings (email, password).
- Placing orders over $500.
- Making refund requests.

## Backup Codes

Upon enabling 2FA, 10 single-use backup codes are generated:

- Store these securely (password manager, printed copy).
- Each code can only be used once.
- If running low, regenerate from **Account** > **Security** > **Backup Codes**.

## Disabling 2FA

2FA can be disabled from **Account** > **Security** > **Two-Factor Authentication** > **Disable**.

Requires current password and an OTP verification. Enterprise accounts may have 2FA enforced by their admin and cannot disable it individually.

## Related Articles

- KB-SEC-001: Account Security Best Practices
- KB-ACC-001: Password Reset
