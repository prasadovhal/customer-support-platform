---
document_id: KB-SEC-006
title: Password Policy and Requirements
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

# Password Policy and Requirements

## Overview

Acme Store enforces a strong password policy to protect customer accounts. This article explains the requirements and best practices.

## Password Requirements

All Acme Store account passwords must meet the following criteria:

| Requirement | Minimum |
|-------------|---------|
| Length | 10 characters |
| Uppercase letters | 1 |
| Lowercase letters | 1 |
| Numbers | 1 |
| Special characters | 1 (!@#$%^&*()-_=+) |
| Not on common password list | Required (top 10,000 common passwords blocked) |
| Not reuse of last 5 passwords | Required |

## Recommended Password Practices

### Length Over Complexity

A longer password is more secure than a short complex one. A 16-character passphrase (e.g., "BlueMountainRainyDay!") is stronger than "P@ss!23".

### Use a Password Manager

Password managers generate and store complex, unique passwords for every site. Recommended options:

- **Bitwarden** (free, open-source)
- **1Password** (commercial)
- **Apple Keychain** (built-in for Apple users)
- **Google Password Manager** (built-in for Chrome/Android)

### Never Reuse Passwords

If one site is breached, reused passwords expose all accounts using the same password.

## Password Reset

If you forget your password, reset it from the login page. You need access to your registered email. See KB-ACC-001.

## Automatic Password Expiration

Acme Store does not force periodic password expiration (in line with NIST SP 800-63B guidelines). However, passwords are automatically invalidated if:

- A breach is detected affecting your account.
- You request a reset.
- A suspicious login pattern is detected.

## What to Do If Your Password Is Compromised

1. Change your Acme Store password immediately.
2. Change the same password on any other sites where it was used.
3. Enable 2FA (KB-ACC-003).
4. Review recent account activity.

## Password Sharing Policy

Password sharing is prohibited. Each user account must use their own unique credentials. Business accounts with multiple users should use the multi-user management feature (KB-ACC-005).

## Related Articles

- KB-ACC-001: Password Reset
- KB-ACC-003: Two-Factor Authentication
- KB-SEC-001: Account Security Best Practices
