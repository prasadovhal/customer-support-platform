---
document_id: KB-ACC-001
title: Password Reset and Account Security
category: account
subcategory: security
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

# Password Reset and Account Security

**Version 2.0 — Effective January 1, 2026**

## Password Reset

### Self-Service Password Reset

1. Go to the Acme Store login page.
2. Click **"Forgot Password?"** below the login form.
3. Enter the email address associated with your account.
4. Check your email for a password reset link (valid for 30 minutes).
5. Click the link and set a new password.

**Not receiving the email?**
- Check your spam/junk folder.
- Ensure you are using the email address registered with Acme Store.
- Allow up to 5 minutes for delivery.
- If still not received, contact support at support@acmestore.example.

### Password Requirements

Passwords must be:
- At least 12 characters long
- Contain at least one uppercase letter
- Contain at least one number
- Contain at least one special character

Passwords cannot be reused (last 5 passwords are remembered).

## Account Lockout

After **5 consecutive failed login attempts**, your account is temporarily locked for 30 minutes.

After the lockout period, you may try again or use the password reset process.

If you are locked out due to suspected unauthorized access, contact support immediately.

## Two-Factor Authentication (2FA)

Acme Store supports 2FA via:
- Authenticator app (TOTP — compatible with Google Authenticator, Authy, etc.)
- SMS (less secure — authenticator app recommended)

To enable 2FA: Account Settings > Security > Two-Factor Authentication.

2FA is strongly recommended for all accounts, especially business and enterprise accounts.

## Suspicious Account Activity

If you notice:
- Orders you did not place
- Changes to your email, password, or shipping address you did not make
- Login notifications from unknown locations

**Act immediately:**
1. Change your password.
2. Enable 2FA if not already enabled.
3. Contact Acme Store security at security@acmestore.example.
4. Review and cancel any unauthorized orders.

Acme Store will never ask for your password via email, chat, or phone.

## Account Email Change

To change your account email address, go to Account Settings > Profile. This is a sensitive operation — a verification email will be sent to both your old and new email addresses.

Email changes require human agent approval if the old email address is no longer accessible.
