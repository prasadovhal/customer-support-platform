---
document_id: KB-TRB-002
title: App and Website Login Issues
category: troubleshooting
source: Acme Store Support Knowledge Base
source_type: synthetic
version: "1.0"
effective_from: "2026-01-01"
effective_to: null
product_scope: all
customer_segment: all
language: en
---

# App and Website Login Issues

## Overview

This article helps resolve common login problems on the Acme Store website and mobile app.

## Issue: Forgot Password

If you cannot remember your password:

1. Go to the login page and click **Forgot Password**.
2. Enter your registered email address.
3. Check your email for the reset link (valid for 30 minutes).
4. Click the link and set a new password.

If you do not receive the email: check spam folder; verify the email address; try requesting again after 5 minutes.

For persistent issues, see KB-ACC-001.

## Issue: "Incorrect Password" Error

If your password is rejected:

- Ensure Caps Lock is off.
- Clear your browser cache and cookies, then retry.
- Use a different browser or private/incognito window.
- After 5 failed attempts, account is temporarily locked for 15 minutes.

## Issue: Account Locked

Accounts are temporarily locked after 5 consecutive failed login attempts (15-minute cooldown) or permanently after suspicious activity.

To unlock:

- Wait 15 minutes and retry.
- If permanently locked, contact support or reset your password.

## Issue: "Account Not Found" Error

- Verify you are using the correct email address.
- Check if you have multiple email addresses and try each.
- You may have signed up with a social login (Google, Apple) — try those.

## Issue: Social Login Not Working

If logging in with Google or Apple fails:

1. Ensure your social account has not been changed or deleted.
2. Revoke and re-grant Acme Store permissions from your Google/Apple account settings.
3. Try logging in with your email and password instead (use Forgot Password to set a password).

## Issue: 2FA Code Not Working

- Ensure your device's clock is accurate (authenticator apps rely on time sync).
- Try requesting a new SMS code.
- Use a backup code (see KB-ACC-003).

## Issue: Stuck in Redirect Loop

Clear your browser cookies and cache for acmestore.com:

- Chrome: Settings > Privacy > Clear Browsing Data
- Firefox: Options > Privacy > Clear History
- Safari: Preferences > Privacy > Manage Website Data

## Related Articles

- KB-ACC-001: Password Reset
- KB-ACC-003: Two-Factor Authentication
- KB-TRB-003: Mobile App Troubleshooting
