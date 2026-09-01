---
document_id: KB-TRB-010
title: Network Equipment Setup and Troubleshooting
category: troubleshooting
source: Acme Store Support Knowledge Base
source_type: synthetic
version: "1.0"
effective_from: "2026-01-01"
effective_to: null
product_scope: networking
customer_segment: all
language: en
---

# Network Equipment Setup and Troubleshooting

## Overview

This article covers setup and troubleshooting for Wi-Fi routers, mesh systems, range extenders, and switches sold by Acme Store.

## Router Initial Setup

1. Connect the router to your modem using an Ethernet cable (WAN/Internet port).
2. Connect your computer to the router via Ethernet or Wi-Fi (default SSID and password are on the label).
3. Open a browser and navigate to the router's admin page (commonly 192.168.1.1 or 192.168.0.1).
4. Follow the setup wizard: set a custom SSID, password, and admin password.

## No Internet After Setup

1. Confirm the Ethernet cable is connected to the WAN/Internet port (not LAN ports).
2. Restart modem first, then router (wait 30 seconds between each restart).
3. Check ISP status — the issue may be on your ISP's end.
4. Verify your ISP requires a specific login (PPPoE) and enter credentials in the router settings.
5. Contact ISP to confirm if MAC address registration is required.

## Wi-Fi Signal Weak in Certain Rooms

1. Place the router in a central location, elevated, and away from walls.
2. Avoid placing near microwaves, cordless phones, or large metal objects.
3. Use 5 GHz for speed (shorter range) and 2.4 GHz for range (more interference).
4. Consider adding a mesh node or range extender.

## Devices Dropping Off the Network

1. Reserve IP addresses (DHCP reservation) for frequently used devices.
2. Ensure the router is not overheating — check ventilation.
3. Update router firmware: admin panel > Firmware Update.
4. Check for QoS settings throttling certain devices.

## Mesh System Not Connecting

1. Place the satellite node within 30 feet of the main router during initial setup.
2. Follow the manufacturer's mesh setup procedure — often requires the companion app.
3. After initial sync, move the satellite to the desired location.

## Port Forwarding

For gaming, cameras, or servers requiring open ports:

1. Log into the router admin panel.
2. Navigate to **Port Forwarding** or **NAT** settings.
3. Create a rule: specify the port range, protocol (TCP/UDP), and device IP address.
4. Assign a static IP to the device to prevent IP changes breaking the rule.

## Related Articles

- KB-TRB-001: General Connectivity Issues
- KB-PRD-006: Networking Equipment Guide
