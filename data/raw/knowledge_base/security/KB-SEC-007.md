---
document_id: KB-SEC-007
title: Device Security for Connected Products
category: security
source: Acme Store Security Team
source_type: synthetic
version: "1.0"
effective_from: "2026-01-01"
effective_to: null
product_scope: networking,home_appliances
customer_segment: all
language: en
---

# Device Security for Connected Products

## Overview

Smart home devices, routers, and IoT products create new attack surfaces in your home network. This article outlines security best practices for connected products purchased from Acme Store.

## Router Security

Your router is the gateway to all devices on your network.

### Immediate Setup Steps

1. **Change the default admin password** — never leave factory default (e.g., "admin/admin").
2. **Update firmware** — manufacturers release security patches; apply immediately.
3. **Disable remote management** — unless you specifically need it.
4. **Use WPA3 encryption** — or at minimum WPA2. Never use WEP.
5. **Change the default SSID** — avoid revealing your router brand.

### Network Segmentation

Create separate Wi-Fi networks:

- **Main network**: For trusted devices (computers, phones).
- **IoT/Guest network**: For smart home devices, TVs, guests.

This limits the impact if an IoT device is compromised — it cannot access your main network.

## Smart Home Device Security

1. **Change default credentials** — all smart home devices ship with default passwords; change them immediately.
2. **Keep devices updated** — enable automatic firmware updates.
3. **Disable unnecessary features** — if you don't use remote access, disable it.
4. **Use the official app** — avoid third-party apps with excessive permissions.
5. **Audit device permissions** — review app permissions; camera devices should not access your contacts.

## Camera and Surveillance Device Security

IP cameras require special attention:

- Use complex passwords for camera admin accounts.
- Do not expose cameras directly to the internet; use a VPN for remote access.
- Regularly check camera activity logs.
- Use end-to-end encrypted storage for recordings.

## What to Do If a Device Is Compromised

1. Disconnect the device from your network immediately.
2. Factory reset the device.
3. Update firmware before reconnecting.
4. Change all passwords on accounts linked to the device.
5. Check for unusual activity on your network (unusual outgoing connections).

## Related Articles

- KB-TRB-001: Connectivity Troubleshooting
- KB-TRB-007: Smart Home Setup
- KB-TRB-010: Network Equipment
