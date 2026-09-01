"""
Acme Store — Synthetic Data Generator
Generates all datasets for the Enterprise Customer Support AI/ML Platform.
Usage: python scripts/generate_all_data.py --seed 42
"""

import argparse
import csv
import json
import os
import random
import string
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# ── helpers ──────────────────────────────────────────────────────────────────

def rand_date(rng, start, end):
    delta = end - start
    return start + timedelta(days=rng.randint(0, delta.days))

def fmt(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def fmt_date(dt):
    return dt.strftime("%Y-%m-%d")

def tracking_number(rng):
    return "TRACK-" + "".join(rng.choices(string.ascii_uppercase + string.digits, k=8))

# ── customers ─────────────────────────────────────────────────────────────────

FIRST_NAMES = [
    "James","Mary","Robert","Patricia","John","Jennifer","Michael","Linda",
    "David","Barbara","William","Elizabeth","Richard","Susan","Joseph","Jessica",
    "Thomas","Sarah","Charles","Karen","Christopher","Lisa","Daniel","Nancy",
    "Matthew","Betty","Anthony","Margaret","Mark","Sandra","Donald","Ashley",
    "Steven","Dorothy","Paul","Kimberly","Andrew","Emily","Kenneth","Donna",
    "Joshua","Michelle","Kevin","Carol","Brian","Amanda","George","Melissa",
    "Timothy","Deborah","Ronald","Stephanie","Edward","Rebecca","Jason","Sharon",
    "Jeffrey","Laura","Ryan","Cynthia","Jacob","Kathleen","Gary","Amy",
    "Nicholas","Angela","Eric","Shirley","Jonathan","Anna","Stephen","Brenda",
    "Larry","Pamela","Justin","Emma","Scott","Nicole","Brandon","Helen","Frank",
    "Samantha","Benjamin","Katherine","Gregory","Christine","Samuel","Debra",
    "Raymond","Rachel","Patrick","Carolyn","Alexander","Janet","Jack","Catherine",
    "Dennis","Maria","Jerry","Heather","Tyler","Diane","Aaron","Julie"
]

LAST_NAMES = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
    "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson",
    "Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson","White",
    "Harris","Sanchez","Clark","Ramirez","Lewis","Robinson","Walker","Young",
    "Allen","King","Wright","Scott","Torres","Nguyen","Hill","Flores","Green",
    "Adams","Nelson","Baker","Hall","Rivera","Campbell","Mitchell","Carter",
    "Roberts","Gomez","Phillips","Evans","Turner","Diaz","Parker","Cruz",
    "Edwards","Collins","Reyes","Stewart","Morris","Morales","Murphy","Cook",
    "Rogers","Gutierrez","Ortiz","Morgan","Cooper","Peterson","Bailey","Reed",
    "Kelly","Howard","Ramos","Kim","Cox","Ward","Richardson","Watson","Brooks",
    "Chavez","Wood","James","Bennett","Gray","Mendoza","Ruiz","Hughes","Price",
    "Alvarez","Castillo","Sanders","Patel","Myers","Long","Ross","Foster","Jimenez"
]

US_STATES = [
    ("CA","Los Angeles"),("CA","San Francisco"),("CA","San Diego"),
    ("NY","New York"),("NY","Buffalo"),("TX","Houston"),("TX","Dallas"),
    ("TX","Austin"),("FL","Miami"),("FL","Orlando"),("IL","Chicago"),
    ("PA","Philadelphia"),("OH","Columbus"),("GA","Atlanta"),("NC","Charlotte"),
    ("MI","Detroit"),("WA","Seattle"),("AZ","Phoenix"),("MA","Boston"),
    ("CO","Denver"),("TN","Nashville"),("OR","Portland"),("NV","Las Vegas"),
    ("MN","Minneapolis"),("WI","Milwaukee"),("MO","St. Louis"),("VA","Richmond"),
    ("NJ","Newark"),("IN","Indianapolis"),("MD","Baltimore")
]

SEGMENTS = (["standard"]*60 + ["premium"]*25 + ["business"]*10 + ["enterprise"]*5)
STATUSES = (["active"]*85 + ["inactive"]*10 + ["suspended"]*5)
LANGUAGES = (["en"]*80 + ["es"]*12 + ["fr"]*8)

def generate_customers(rng, n=1000):
    rows = []
    now = datetime(2026, 1, 1)
    for i in range(1, n + 1):
        fn = rng.choice(FIRST_NAMES)
        ln = rng.choice(LAST_NAMES)
        email_tag = rng.randint(1, 999)
        state, city = rng.choice(US_STATES)
        reg = rand_date(rng, datetime(2020, 1, 1), datetime(2025, 12, 31))
        rows.append({
            "customer_id": f"CUS-{i:04d}",
            "first_name": fn,
            "last_name": ln,
            "email": f"{fn.lower()}.{ln.lower()}{email_tag}@syntheticmail.example",
            "phone": f"+1-{rng.randint(200,999)}-{rng.randint(200,999)}-{rng.randint(1000,9999)}",
            "customer_segment": rng.choice(SEGMENTS),
            "account_status": rng.choice(STATUSES),
            "country": "US",
            "state": state,
            "city": city,
            "registration_date": fmt_date(reg),
            "preferred_language": rng.choice(LANGUAGES),
            "created_at": fmt(reg),
            "updated_at": fmt(rand_date(rng, reg, now)),
        })
    return rows

# ── products ──────────────────────────────────────────────────────────────────

PRODUCT_TEMPLATES = {
    "Laptops": [
        ("AcmePro X{n} Laptop","14-inch business laptop, {r}GB RAM, {s}GB SSD"),
        ("SwiftBook {n} Ultra","Slim ultrabook with {r}GB RAM and long battery life"),
        ("ProEdge {n}S","Performance laptop for professionals, {r}GB RAM"),
    ],
    "Smartphones": [
        ("NovPhone {n} Pro","5G smartphone, {r}MP camera, AMOLED display"),
        ("ZenMobile {n}","Mid-range smartphone with {r}GB storage"),
        ("AcmeDial X{n}","Flagship smartphone with triple camera system"),
    ],
    "Tablets": [
        ("TabMax {n}","10-inch tablet, {r}GB RAM, ideal for productivity"),
        ("AcmeSlate {n} Pro","Professional-grade tablet with stylus support"),
        ("LiteTab {n}","Lightweight 8-inch tablet for everyday use"),
    ],
    "Electronics": [
        ("AcmeSpark {n}","General electronics device with advanced features"),
        ("TechCore {n} Pro","Smart device with connectivity features"),
        ("DigiLink {n}","Digital connectivity device"),
    ],
    "Accessories": [
        ("AcmeCase {n}","Protective case compatible with multiple devices"),
        ("PowerLink {n} Cable","USB-C charging cable, {r}W fast charge"),
        ("SlimHub {n}","Portable USB hub with {r} ports"),
    ],
    "HomeAppliances": [
        ("AcmeBreeze {n}","Smart air purifier with HEPA filter"),
        ("HomeCore {n} Plus","Energy-efficient home appliance"),
        ("SmartHome {n}","Connected home automation device"),
    ],
    "Wearables": [
        ("AcmeFit {n}","Fitness tracker with heart rate monitor"),
        ("SmartBand {n} Pro","Advanced smartwatch with health monitoring"),
        ("ActivePulse {n}","Sports wearable with GPS tracking"),
    ],
    "Audio": [
        ("NovaSound BT{n}","Bluetooth over-ear headphones, ANC"),
        ("AcmeBuds {n} Pro","True wireless earbuds with noise cancellation"),
        ("SoundBar {n}","Home audio soundbar, {r}W output"),
    ],
    "Networking": [
        ("AcmeRouter {n}","WiFi 6 router, {r} sq ft coverage"),
        ("NetBoost {n} Pro","Mesh networking node"),
        ("LinkPro {n}","Gigabit network switch with {r} ports"),
    ],
    "Gaming": [
        ("AcmePlay {n}","Gaming controller with haptic feedback"),
        ("GameEdge {n} Pro","Gaming headset with surround sound"),
        ("ControlPad {n}","Mechanical gaming keyboard"),
    ],
}

WARRANTY = {
    "Laptops": 24, "Smartphones": 12, "Tablets": 12,
    "Electronics": 12, "Accessories": 6, "HomeAppliances": 24,
    "Wearables": 12, "Audio": 12, "Networking": 12, "Gaming": 12,
}

RETURN_WINDOW = {
    "Laptops": 15, "Smartphones": 15, "Tablets": 15,
    "Electronics": 30, "Accessories": 30, "HomeAppliances": 30,
    "Wearables": 30, "Audio": 30, "Networking": 30, "Gaming": 30,
}

PRICE_RANGE = {
    "Laptops": (499, 2999), "Smartphones": (299, 1499),
    "Tablets": (199, 999), "Electronics": (49, 499),
    "Accessories": (9, 149), "HomeAppliances": (79, 599),
    "Wearables": (49, 399), "Audio": (29, 499),
    "Networking": (49, 399), "Gaming": (29, 199),
}

def generate_products(rng, n=100):
    rows = []
    categories = list(PRODUCT_TEMPLATES.keys())
    per_cat = n // len(categories)
    prod_id = 1
    now = datetime(2026, 1, 1)
    for cat in categories:
        templates = PRODUCT_TEMPLATES[cat]
        for j in range(per_cat):
            tmpl_name, tmpl_desc = rng.choice(templates)
            r = rng.choice([4, 8, 16, 32, 64, 128, 256])
            s = rng.choice([128, 256, 512, 1024])
            name = tmpl_name.format(n=rng.randint(1, 99), r=r, s=s)
            desc = tmpl_desc.format(n=rng.randint(1, 99), r=r, s=s)
            lo, hi = PRICE_RANGE[cat]
            price = round(rng.uniform(lo, hi), 2)
            sku = f"SKU-{cat[:3].upper()}-{prod_id:04d}"
            created = rand_date(rng, datetime(2022, 1, 1), datetime(2025, 1, 1))
            stock = rng.choices(
                ["in_stock", "out_of_stock", "discontinued"],
                weights=[80, 15, 5]
            )[0]
            rows.append({
                "product_id": f"PROD-{prod_id:03d}",
                "sku": sku,
                "product_name": name,
                "category": cat,
                "subcategory": cat,
                "description": desc,
                "price": f"{price:.2f}",
                "currency": "USD",
                "stock_status": stock,
                "warranty_months": WARRANTY[cat],
                "return_window_days": RETURN_WINDOW[cat],
                "is_active": "true" if stock != "discontinued" else "false",
                "created_at": fmt(created),
                "updated_at": fmt(rand_date(rng, created, now)),
            })
            prod_id += 1
    return rows

# ── orders ────────────────────────────────────────────────────────────────────

ORDER_STATUSES = [
    "placed","confirmed","processing","shipped","out_for_delivery",
    "delivered","delayed","cancelled","returned","refunded"
]

PAYMENT_METHODS = (
    ["credit_card"]*45 + ["debit_card"]*25 + ["paypal"]*20 +
    ["bank_transfer"]*8 + ["crypto"]*2
)

SHIPPING_METHODS = (
    ["standard"]*50 + ["express"]*30 + ["next_day"]*15 + ["international"]*5
)

def order_payment_status(rng, status):
    if status in ("returned", "refunded"):
        return rng.choice(["refunded", "partially_refunded"])
    if status == "cancelled":
        return rng.choice(["refunded", "failed", "paid"])
    if status == "placed":
        return rng.choice(["pending", "paid"])
    return "paid"

def generate_orders(rng, customers, products, n=5000):
    rows = []
    start = datetime(2024, 1, 1)
    end = datetime(2025, 12, 31)
    now = datetime(2026, 1, 1)
    customer_ids = [c["customer_id"] for c in customers]
    product_ids = [p["product_id"] for p in products]
    product_map = {p["product_id"]: p for p in products}
    weights = [10,8,7,15,10,25,5,8,6,6]
    for i in range(1, n + 1):
        cid = rng.choice(customer_ids)
        pid = rng.choice(product_ids)
        prod = product_map[pid]
        order_date = rand_date(rng, start, end)
        qty = rng.randint(1, 5)
        unit_price = float(prod["price"])
        total = round(unit_price * qty, 2)
        status = rng.choices(ORDER_STATUSES, weights=weights)[0]
        payment_status = order_payment_status(rng, status)
        ship_method = rng.choice(SHIPPING_METHODS)
        tracking = tracking_number(rng)

        if ship_method == "next_day":
            ship_days = 1
        elif ship_method == "express":
            ship_days = rng.randint(2, 4)
        elif ship_method == "international":
            ship_days = rng.randint(10, 30)
        else:
            ship_days = rng.randint(5, 10)

        expected_delivery = order_date + timedelta(days=ship_days)
        if expected_delivery > now:
            expected_delivery = now - timedelta(days=1)

        if status == "delivered":
            actual_delivery = order_date + timedelta(days=rng.randint(ship_days, ship_days + 3))
            if actual_delivery > now:
                actual_delivery = now - timedelta(days=1)
            actual_delivery_str = fmt_date(actual_delivery)
        elif status in ("returned", "refunded"):
            actual_delivery = order_date + timedelta(days=rng.randint(ship_days, ship_days + 3))
            if actual_delivery > now:
                actual_delivery = now - timedelta(days=1)
            actual_delivery_str = fmt_date(actual_delivery)
        else:
            actual_delivery_str = ""

        rows.append({
            "order_id": f"ORD-{i:05d}",
            "customer_id": cid,
            "order_date": fmt_date(order_date),
            "product_id": pid,
            "quantity": qty,
            "unit_price": f"{unit_price:.2f}",
            "total_amount": f"{total:.2f}",
            "currency": "USD",
            "payment_method": rng.choice(PAYMENT_METHODS),
            "payment_status": payment_status,
            "order_status": status,
            "shipping_method": ship_method,
            "tracking_number": tracking,
            "expected_delivery_date": fmt_date(expected_delivery),
            "actual_delivery_date": actual_delivery_str,
            "created_at": fmt(order_date),
            "updated_at": fmt(rand_date(rng, order_date, now)),
        })
    return rows

# ── support tickets ───────────────────────────────────────────────────────────

TICKET_CATEGORIES = [
    "shipping","returns","refunds","payments","orders",
    "products","warranty","account","technical","security"
]

INTENTS = {
    "shipping": ["track_shipment","report_lost_package","report_delayed_delivery",
                 "change_shipping_address","report_failed_delivery","report_wrong_address"],
    "returns": ["initiate_return","check_return_eligibility","return_status",
                "report_damaged_item","report_defective_item"],
    "refunds": ["request_refund","check_refund_status","dispute_charge",
                "report_duplicate_charge","partial_refund_request"],
    "payments": ["payment_failure","update_payment_method","billing_inquiry",
                 "invoice_request","payment_authorization_issue"],
    "orders": ["cancel_order","modify_order","check_order_status",
               "report_wrong_item","missing_item"],
    "products": ["product_inquiry","product_compatibility","product_registration",
                 "product_recommendation","product_defect"],
    "warranty": ["warranty_claim","check_warranty_status","extend_warranty",
                 "warranty_replacement"],
    "account": ["password_reset","account_locked","update_profile","close_account",
                "account_security"],
    "technical": ["setup_issue","connectivity_problem","software_issue",
                  "hardware_malfunction","compatibility_issue"],
    "security": ["unauthorized_access","suspicious_activity","data_breach_concern",
                 "fraud_report","account_compromise"],
}

ASSIGNED_TEAMS = {
    "shipping": "shipping_support",
    "returns": "returns_support",
    "refunds": "billing_support",
    "payments": "billing_support",
    "orders": "general_support",
    "products": "technical_support",
    "warranty": "returns_support",
    "account": "general_support",
    "technical": "technical_support",
    "security": "security_support",
}

TICKET_MESSAGES = {
    "shipping": [
        "I placed an order {days} days ago and my package hasn't arrived yet. The tracking number shows it's still in transit. Can you help?",
        "My tracking shows 'delivered' but I never received my package. I checked with my neighbors and the front desk, no sign of it.",
        "I need to change my delivery address. My order hasn't shipped yet — is it too late to update?",
        "The carrier attempted delivery but I wasn't home. I haven't been able to reschedule a redelivery through their site.",
        "My package has been stuck at the same location for {days} days. The tracking info hasn't updated at all.",
        "I ordered express shipping but it's been {days} days and still nothing. This should have arrived already.",
        "I received a notification that my package was delivered but it's not here. Could it have been delivered to the wrong address?",
        "My order shows it shipped but I never received a tracking number via email. How can I find out where my package is?",
        "I'm moving next week — can I redirect my package to a different address? It hasn't shipped yet.",
        "The delivery attempt failed because the driver couldn't access my building. I need to reschedule for when I'm home.",
    ],
    "returns": [
        "I'd like to return an item I received {days} days ago. It's not what I expected based on the product description.",
        "I received a damaged item in my order. The packaging was intact but the product itself is cracked. I need to return it.",
        "The laptop I bought {days} days ago isn't working properly. I'd like to initiate a return. Is it within the return window?",
        "I'm an enterprise customer. I have a large order I need to return — what's the process for bulk returns?",
        "I opened the box but decided the product isn't what I need. Can I still return it even though it's been opened?",
        "My item arrived defective straight out of the box. I haven't even used it. What's the fastest way to get a replacement?",
        "I purchased a smartphone {days} days ago. I know electronics have a shorter return window — am I still eligible?",
        "I received the wrong item in my shipment. I ordered a blue model but got a red one. Can I exchange or return it?",
        "The product stopped working after just a week of normal use. This seems like a manufacturing defect.",
        "I want to return a gift I received. I have the order number but I'm not the original purchaser. Is that possible?",
    ],
    "refunds": [
        "I returned my order {days} days ago and I still haven't received my refund. Can you check the status?",
        "I was charged twice for the same order. I can see two identical transactions on my credit card statement.",
        "My order was cancelled but the payment hasn't been refunded to my account yet. It's been {days} days.",
        "I received a partial refund but I expected a full refund. Can you explain why it wasn't fully refunded?",
        "I disputed a charge and the bank said it was resolved, but I don't see the credit on my account yet.",
        "I cancelled my order within minutes of placing it but I was still charged. When will I receive my refund?",
        "I'm seeing a pending charge that I don't recognize. I never placed an order for this amount.",
        "My refund was supposed to be processed {days} days ago according to your email. Still nothing in my account.",
        "I returned two items from the same order. I only received a refund for one. What happened to the other?",
        "The refund amount doesn't match what I paid. I paid with a discount code — was that taken into account?",
    ],
    "payments": [
        "My payment keeps failing at checkout even though my card details are correct and I have sufficient funds.",
        "I want to pay via invoice for my business account. How do I set up net-30 payment terms?",
        "My credit card expired and I need to update my payment method for a pending order.",
        "I was charged a different amount than what was shown at checkout. There seems to be a discrepancy.",
        "My PayPal payment shows as completed on PayPal's side but my order still shows payment pending.",
        "I need an official invoice for my order for tax purposes. Can you send me one?",
        "The payment authorization failed even though my bank says the transaction was approved.",
        "I'd like to split my payment across two different cards. Is that an option?",
        "I'm getting an error message saying my billing address doesn't match. I've confirmed it's correct.",
        "I made a bank transfer {days} days ago but my order is still showing payment pending.",
    ],
    "orders": [
        "I need to cancel my order. I just placed it {minutes} minutes ago — is it possible to cancel before it ships?",
        "I accidentally ordered two of the same item. Can I modify the quantity to just one?",
        "I ordered the wrong size/color variant. Can this be changed or do I need to cancel and reorder?",
        "My order shows as processing but I haven't received any shipping confirmation email yet.",
        "One item from my multi-item order arrived but the other is still showing as processing.",
        "I received a confirmation email but when I check my account, I don't see the order listed.",
        "My order was split into two shipments without any notification. When will the second one arrive?",
        "I need my order urgently. Can I upgrade the shipping method after placing the order?",
        "My order shows as delivered but it only partially arrived — some items are missing.",
        "I placed an order {days} days ago and it's still in processing status. When will it ship?",
    ],
    "products": [
        "I'm trying to determine if this laptop is compatible with the external monitor I already own.",
        "Can you help me understand the difference between the two models I'm considering?",
        "I need to register my new product for warranty purposes. The registration link in the box doesn't work.",
        "The product description says it includes a charging cable but mine didn't come with one.",
        "I need a product that can handle {task}. Which items in your catalog would you recommend?",
        "I'm having trouble setting up my new device. The instructions aren't clear.",
        "Is this product compatible with Mac OS? The listing only mentions Windows.",
        "The specs say the battery lasts 8 hours but mine barely lasts 3. Is this a defect?",
        "I need to know if I can use this device in a country with different voltage standards.",
        "Can you tell me if a specific product will be back in stock soon?",
    ],
    "warranty": [
        "My product stopped working and it's still under the manufacturer's warranty. How do I file a claim?",
        "I need to check if my product is still under warranty. I've had it for about {months} months.",
        "My warranty claim was rejected but I believe the damage is a manufacturing defect, not user damage.",
        "I'd like to extend my warranty before it expires. What options are available?",
        "The product was repaired under warranty but the same issue has returned. What are my options?",
        "I lost my proof of purchase. Can I still make a warranty claim using my order number?",
        "My warranty repair is taking longer than expected. When will I get my product back?",
        "I purchased the product as a gift. The recipient wants to register the warranty — is that possible?",
        "The product was replaced under warranty but I'm not satisfied with the replacement model.",
        "What exactly is covered under the standard warranty? I'm not sure if my issue qualifies.",
    ],
    "account": [
        "I can't log into my account. I've tried resetting my password but I'm not receiving the reset email.",
        "I need to update my email address. The current one is from a job I no longer have.",
        "My account seems to have been hacked. I see order history for purchases I didn't make.",
        "I want to close my account and delete all my personal data. What's the process?",
        "I'm locked out of my account after too many failed login attempts. How do I unlock it?",
        "I have two accounts with the same email. I want to merge the order history into one account.",
        "I need to update my billing address. I've moved and need to update my details.",
        "I'm not receiving order confirmation emails even though my address is correct.",
        "Someone tried to access my account from an unfamiliar location. I received a security alert.",
        "I want to remove a saved payment method from my account but can't find the option.",
    ],
    "technical": [
        "My device won't turn on even after charging it fully overnight. I've tried holding the power button.",
        "I'm having connectivity issues — the device keeps disconnecting from WiFi every few minutes.",
        "The software keeps crashing whenever I try to open a specific feature. I've tried reinstalling.",
        "I followed the setup instructions but the device isn't being recognized by my computer.",
        "The display has dead pixels. I noticed them right after unboxing. This seems like a defect.",
        "My device is overheating during normal use. The fan seems to be running constantly.",
        "I can't get the Bluetooth pairing to work between my new device and my phone.",
        "The device is running very slowly after a recent software update. How do I roll back?",
        "The camera on my device is producing blurry images even in good lighting conditions.",
        "I'm getting error code E-{code} when trying to use the device. What does this mean?",
    ],
    "security": [
        "I received an email claiming to be from Acme Store asking for my password. I think it's a phishing attempt.",
        "I noticed several unauthorized purchases on my account that I didn't make. I need help immediately.",
        "I received a notification about a login from a location I've never been to. I think my account is compromised.",
        "I want to report a suspicious seller listing on your platform that seems fraudulent.",
        "My credit card was charged by Acme Store but I haven't placed any orders recently.",
        "I'm concerned about how my personal data is being used. I want to request a copy of my data.",
        "Someone appears to have used my account to place orders. I need all recent orders cancelled.",
        "I received a package I didn't order to my address. I'm worried someone is using my information.",
        "The security question on my account has been changed without my knowledge.",
        "I want to enable two-factor authentication on my account. How do I set it up?",
    ],
}

SUBCATEGORIES = {
    "shipping": ["tracking","lost_package","delayed","address_change","failed_delivery","wrong_address"],
    "returns": ["return_request","damaged","defective","return_status","exchange","policy"],
    "refunds": ["refund_status","duplicate_charge","partial","cancellation","timeline"],
    "payments": ["payment_failure","invoice","update_method","authorization","billing"],
    "orders": ["cancellation","modification","status","missing_item","wrong_item"],
    "products": ["inquiry","compatibility","registration","recommendation","defect"],
    "warranty": ["claim","status","extension","replacement","coverage"],
    "account": ["password","email","security","closure","profile","merge"],
    "technical": ["setup","connectivity","software","hardware","compatibility"],
    "security": ["unauthorized_access","fraud","phishing","data","account_compromise"],
}

RESOLUTIONS = {
    "shipping": [
        "Initiated investigation with carrier. Customer will be contacted within 2 business days.",
        "Provided tracking information and escalated to carrier for priority tracing.",
        "Processed reshipment of order to correct address at no extra charge.",
        "Filed lost package claim with carrier. Refund or replacement offered.",
        "Rescheduled delivery for next business day.",
    ],
    "returns": [
        "Return label issued. Customer to ship item within 7 days.",
        "Return approved and replacement shipped express.",
        "Full refund processed after confirming item condition.",
        "Exception approved due to damaged item — extended return window applied.",
        "Enterprise return processed per contract terms.",
    ],
    "refunds": [
        "Refund of ${amount} processed to original payment method. Allow 3-5 business days.",
        "Duplicate charge reversed. Credit will appear within 3-7 business days.",
        "Partial refund of ${amount} applied per return policy.",
        "Refund initiated; customer advised to allow up to 10 days for bank processing.",
        "Full refund approved for cancelled order.",
    ],
    "payments": [
        "Payment method updated successfully. Order will now process.",
        "Invoice generated and sent to customer email.",
        "Payment issue escalated to billing team for manual review.",
        "Customer advised to contact bank; charge appears to be a temporary authorization hold.",
        "Alternative payment method accepted; order confirmed.",
    ],
    "orders": [
        "Order successfully cancelled. Refund initiated.",
        "Order modification applied before shipment cutoff.",
        "Order confirmed active; shipping label generated.",
        "Missing item reshipped at no charge.",
        "Wrong item return label issued; correct item shipped.",
    ],
    "products": [
        "Compatibility confirmed with customer's existing setup.",
        "Product registration completed manually by support agent.",
        "Missing accessory dispatched as separate shipment.",
        "Technical specifications shared with customer.",
        "Replacement product shipped under warranty.",
    ],
    "warranty": [
        "Warranty claim approved. Replacement unit shipped.",
        "Device sent for repair under warranty. ETA 7-10 business days.",
        "Warranty extended by 12 months as goodwill gesture.",
        "Claim rejected — damage determined to be outside warranty scope. Repair quote provided.",
        "Out-of-warranty repair approved at discounted rate.",
    ],
    "account": [
        "Password reset email resent. Customer advised to check spam folder.",
        "Email address updated successfully.",
        "Account unlocked. Security review completed.",
        "Account closure processed. Data deletion scheduled per policy.",
        "Two-factor authentication enabled on customer's account.",
    ],
    "technical": [
        "Issue resolved with firmware update. Customer confirmed device working.",
        "Remote diagnostic completed. Factory reset recommended and performed.",
        "Hardware defect confirmed. Replacement unit authorized.",
        "Driver update resolved connectivity issue.",
        "Escalated to engineering team for further investigation.",
    ],
    "security": [
        "Unauthorized access confirmed. Account secured, password reset forced, customer notified.",
        "Fraudulent orders cancelled. Refund initiated. Account secured.",
        "Phishing report logged. Customer advised on account security measures.",
        "Data request processed per GDPR guidelines.",
        "Account temporarily suspended pending security review.",
    ],
}

RESOLUTION_CODES = {
    "shipping": ["CARRIER_INVESTIGATION","RESHIPPED","REFUNDED","TRACKING_PROVIDED","DELIVERY_RESCHEDULED"],
    "returns": ["RETURN_APPROVED","REPLACEMENT_SENT","REFUND_PROCESSED","EXCEPTION_APPLIED","ENTERPRISE_RETURN"],
    "refunds": ["REFUND_PROCESSED","DUPLICATE_REVERSED","PARTIAL_REFUND","REFUND_INITIATED","FULL_REFUND"],
    "payments": ["PAYMENT_UPDATED","INVOICE_SENT","ESCALATED_BILLING","AUTHORIZATION_HOLD","ALT_PAYMENT"],
    "orders": ["CANCELLED","MODIFIED","CONFIRMED","RESHIPPED","WRONG_ITEM_RESOLVED"],
    "products": ["COMPATIBILITY_CONFIRMED","REGISTRATION_DONE","ACCESSORY_SENT","INFO_PROVIDED","WARRANTY_REPLACEMENT"],
    "warranty": ["WARRANTY_REPLACEMENT","WARRANTY_REPAIR","WARRANTY_EXTENDED","CLAIM_REJECTED","REPAIR_QUOTE"],
    "account": ["PASSWORD_RESET","EMAIL_UPDATED","ACCOUNT_UNLOCKED","ACCOUNT_CLOSED","2FA_ENABLED"],
    "technical": ["FIRMWARE_UPDATE","FACTORY_RESET","HARDWARE_REPLACEMENT","DRIVER_UPDATE","ESCALATED_ENGINEERING"],
    "security": ["ACCOUNT_SECURED","FRAUD_RESOLVED","PHISHING_LOGGED","DATA_REQUEST_PROCESSED","ACCOUNT_SUSPENDED"],
}

def generate_tickets(rng, customers, products, orders, n=1000):
    rows = []
    now = datetime(2026, 1, 1)
    start = datetime(2024, 6, 1)
    cust_ids = [c["customer_id"] for c in customers]
    cust_map = {c["customer_id"]: c for c in customers}
    prod_ids = [p["product_id"] for p in products]
    order_ids = [o["order_id"] for o in orders]
    order_map = {o["order_id"]: o for o in orders}

    channels = (["web"]*30 + ["email"]*35 + ["chat"]*25 + ["phone"]*10)
    priorities = (["P0"]*3 + ["P1"]*12 + ["P2"]*50 + ["P3"]*35)
    sentiments = (["positive"]*10 + ["neutral"]*30 + ["negative"]*45 + ["angry"]*15)
    statuses = (["open"]*15 + ["in_progress"]*20 + ["waiting_for_customer"]*10 +
                ["resolved"]*30 + ["closed"]*25)

    for i in range(1, n + 1):
        cid = rng.choice(cust_ids)
        cat = rng.choice(TICKET_CATEGORIES)
        intent = rng.choice(INTENTS[cat])
        subcat = rng.choice(SUBCATEGORIES[cat])
        created = rand_date(rng, start, now - timedelta(days=1))
        channel = rng.choice(channels)
        priority = rng.choice(priorities)
        sentiment = rng.choice(sentiments)
        team = ASSIGNED_TEAMS[cat]
        # enterprise customers sometimes get enterprise team
        if cust_map[cid]["customer_segment"] == "enterprise" and rng.random() < 0.6:
            team = "enterprise_support"
        status = rng.choice(statuses)

        msg_template = rng.choice(TICKET_MESSAGES[cat])
        days = rng.randint(2, 30)
        minutes = rng.randint(5, 120)
        months = rng.randint(3, 24)
        code = rng.randint(100, 999)
        task = rng.choice(["video editing", "gaming", "office work", "photo editing"])
        amount = round(rng.uniform(20, 500), 2)
        message = msg_template.format(
            days=days, minutes=minutes, months=months,
            code=code, task=task, amount=amount
        )
        subject_map = {
            "shipping": f"Issue with my shipment — order help needed",
            "returns": f"Return request for recent order",
            "refunds": f"Refund not received / billing issue",
            "payments": f"Payment problem on my account",
            "orders": f"Question about my order",
            "products": f"Product question / issue",
            "warranty": f"Warranty claim request",
            "account": f"Account access issue",
            "technical": f"Technical support needed",
            "security": f"Security concern — urgent",
        }
        subject = subject_map[cat]

        order_id = ""
        if rng.random() < 0.7 and order_ids:
            order_id = rng.choice(order_ids)
            oid_cid = order_map[order_id]["customer_id"]
            if oid_cid != cid and rng.random() < 0.7:
                order_id = ""

        prod_id = ""
        if rng.random() < 0.6:
            prod_id = rng.choice(prod_ids)

        escalated = rng.random() < 0.15
        escalation_reason = ""
        if escalated:
            escalation_reason = rng.choice([
                "Customer requested supervisor",
                "Issue unresolved after multiple contacts",
                "High-value order involved",
                "Security concern flagged",
                "Policy exception required",
                "Customer expressed extreme dissatisfaction",
            ])

        resolution = ""
        resolution_code = ""
        resolution_time = ""
        satisfaction = ""

        if status in ("resolved", "closed"):
            resolution = rng.choice(RESOLUTIONS[cat]).replace("${amount}", str(round(rng.uniform(20, 500), 2)))
            resolution_code = rng.choice(RESOLUTION_CODES[cat])
            resolution_time = str(rng.randint(10, 1440))
            satisfaction = str(rng.choices([1,2,3,4,5], weights=[5,10,20,40,25])[0])

        first_response = str(rng.randint(2, 240))

        rows.append({
            "ticket_id": f"TKT-{i:04d}",
            "customer_id": cid,
            "order_id": order_id,
            "product_id": prod_id,
            "created_at": fmt(created),
            "channel": channel,
            "subject": subject,
            "message": message,
            "category": cat,
            "subcategory": subcat,
            "intent": intent,
            "priority": priority,
            "sentiment": sentiment,
            "assigned_team": team,
            "status": status,
            "resolution": resolution,
            "resolution_code": resolution_code,
            "resolution_time_minutes": resolution_time,
            "escalated": str(escalated).lower(),
            "escalation_reason": escalation_reason,
            "customer_satisfaction": satisfaction,
            "first_response_time_minutes": first_response,
        })
    return rows

# ── conversations ─────────────────────────────────────────────────────────────

CONV_SCENARIOS = [
    "simple_faq","order_status","delayed_delivery","return_request","refund_request",
    "damaged_product","technical_troubleshooting","account_issue","payment_issue",
    "multi_turn_clarification","policy_exception","human_escalation","tool_dependent","adversarial"
]

CONV_TEMPLATES = {
    "simple_faq": {
        "customer": [
            "Hi, I have a quick question about your return policy.",
            "What's the standard return window for electronics?",
            "Thank you!",
        ],
        "agent": [
            "Hello! I'd be happy to help you with that.",
            "For electronics such as laptops, smartphones, and tablets, we have a 15-day return window from the date of delivery. For all other products, the standard return window is 30 days.",
            "You're welcome! Is there anything else I can help you with today?",
        ],
        "intent": "check_return_policy",
        "resolution": "resolved",
    },
    "order_status": {
        "customer": [
            "Hi, I'd like to know the status of my order.",
            "It's order number ORD-{order_id}.",
            "Thank you for checking!",
        ],
        "agent": [
            "Of course! Could you please provide your order number?",
            "I can see your order ORD-{order_id} was placed on {date} and is currently in '{status}' status. {extra}",
            "You're welcome! Feel free to reach out if you need anything else.",
        ],
        "intent": "check_order_status",
        "resolution": "resolved",
    },
    "delayed_delivery": {
        "customer": [
            "I placed an order {days} days ago and it still hasn't arrived.",
            "The order number is ORD-{order_id}. The expected delivery was last week.",
            "Is there anything you can do to speed this up? I need it urgently.",
        ],
        "agent": [
            "I'm sorry to hear your order is delayed. Let me look into that for you.",
            "I can see order ORD-{order_id} is currently delayed. I've escalated this to our carrier investigation team. You should receive an update within 48 hours.",
            "I understand the urgency. If the carrier can't confirm delivery within 3 business days, we will reship at no cost or issue a full refund — whichever you prefer.",
        ],
        "intent": "report_delayed_delivery",
        "resolution": "resolved",
    },
    "return_request": {
        "customer": [
            "I want to return a product I bought recently.",
            "I ordered a laptop {days} days ago and it's not working properly.",
            "Yes, I have the order number. It's ORD-{order_id}.",
            "That would be great, thank you.",
        ],
        "agent": [
            "I can help you with that! Could you provide more details about the issue and your order number?",
            "I'm sorry to hear that. Let me check your order details.",
            "I've located your order. Since it's within the return window, I can initiate a return for you. Would you like a refund or a replacement?",
            "I've initiated the return. You'll receive a prepaid return label via email within 24 hours. Once we receive the item, we'll process your request within 3-5 business days.",
        ],
        "intent": "initiate_return",
        "resolution": "resolved",
    },
    "refund_request": {
        "customer": [
            "Hi, I returned an item {days} days ago and I still haven't received my refund.",
            "My order number is ORD-{order_id}. The return tracking shows it was delivered to your warehouse.",
            "How long does the refund actually take?",
        ],
        "agent": [
            "I apologize for the delay. Let me look up your return and refund status right away.",
            "I can see the return for ORD-{order_id} was received. It appears the refund is still being processed. I'm going to flag this for priority review.",
            "Refunds typically take 3-5 business days after inspection. I've escalated this so you should see the credit within 2 business days. You'll receive a confirmation email once it's processed.",
        ],
        "intent": "check_refund_status",
        "resolution": "resolved",
    },
    "damaged_product": {
        "customer": [
            "I received a damaged item in my order. The screen is cracked.",
            "I just opened it today. Order number is ORD-{order_id}.",
            "I'd like a replacement, not a refund.",
        ],
        "agent": [
            "I'm very sorry to hear that. Receiving a damaged item is completely unacceptable. Let me pull up your order.",
            "I've found your order ORD-{order_id}. Could you please send a photo of the damage to returns@acmestore.example with your order number? This will help us process your claim faster.",
            "Absolutely — I've noted your preference for a replacement. Once we receive the photo, we'll ship a replacement unit with express delivery at no charge. Your original item can be returned using the prepaid label we'll email you.",
        ],
        "intent": "report_damaged_item",
        "resolution": "resolved",
    },
    "technical_troubleshooting": {
        "customer": [
            "My device won't connect to WiFi even though all my other devices connect fine.",
            "I've already tried restarting it and forgetting the network. Nothing works.",
            "What else can I try before sending it in?",
        ],
        "agent": [
            "I'm sorry you're having connectivity issues. Let's work through this step by step.",
            "Since you've already restarted and forgotten the network, let's try resetting the network settings. Go to Settings > General > Reset > Reset Network Settings. Note that this will remove all saved WiFi passwords.",
            "If that doesn't resolve it, the issue may be a hardware defect. I can arrange a warranty inspection. Since your device is still under warranty, there would be no cost. Would you like me to initiate a warranty service request?",
        ],
        "intent": "connectivity_problem",
        "resolution": "resolved",
    },
    "account_issue": {
        "customer": [
            "I can't log into my account. I've been trying for the past hour.",
            "I've already used the password reset link twice but I'm not getting the email.",
            "Yes, I checked spam. Nothing there either.",
        ],
        "agent": [
            "I'm sorry you're having trouble logging in. Let me help you get back into your account.",
            "I can see your account in our system. The reset emails were sent but may have been blocked by your email provider. Let me verify your identity another way — could you confirm the last four digits of the payment method on file?",
            "Thank you for confirming. I've manually triggered a reset link to an alternate verification method. You should receive it within 5 minutes. I've also whitelisted your email so future reset emails won't be blocked.",
        ],
        "intent": "password_reset",
        "resolution": "resolved",
    },
    "payment_issue": {
        "customer": [
            "My payment keeps failing at checkout. I've tried twice.",
            "I'm using a Visa credit card and there's definitely enough money in the account.",
            "I called my bank and they said the transaction isn't even reaching them.",
        ],
        "agent": [
            "I'm sorry for the trouble at checkout. Payment failures like this are frustrating. Let me look into what might be happening.",
            "Sometimes our payment processor has issues with certain card configurations. Could you try clearing your browser cache and using a private/incognito window? Alternatively, try PayPal as a temporary workaround.",
            "I've also noted your account for our technical team to investigate the underlying cause. If the incognito window doesn't work, please contact us back and we can manually process the order on our end.",
        ],
        "intent": "payment_failure",
        "resolution": "resolved",
    },
    "multi_turn_clarification": {
        "customer": [
            "Hi, I have a question about an order.",
            "It's complicated. I ordered something, it arrived, but I'm not sure if I want to keep it.",
            "It's a laptop. I got it about 12 days ago.",
            "Oh, I didn't know that. In that case, I'd like to start the return.",
        ],
        "agent": [
            "Of course! I'm happy to help. Can you tell me more about the situation?",
            "I understand. What specifically are you unsure about? Is it a quality issue, or are you reconsidering whether you need it?",
            "Good news — laptops have a 15-day return window, so you're still within the return period. Your order needs to be returned within the next 3 days. Would you like me to initiate the return process now?",
            "I've initiated the return for your laptop. You'll receive a prepaid shipping label within 24 hours. Please ship it back within 7 days of receiving the label.",
        ],
        "intent": "initiate_return",
        "resolution": "resolved",
    },
    "policy_exception": {
        "customer": [
            "I know I'm outside the normal return window, but I have a special situation.",
            "I was in hospital for 3 weeks and couldn't deal with the return. My laptop is {days} days old.",
            "I understand the policy, but is there really nothing you can do?",
        ],
        "agent": [
            "I'm very sorry to hear about your hospitalization. I understand this was beyond your control.",
            "Our standard electronics return window is 15 days, but we do have a hardship exception process. I'm going to escalate this to our customer care team with a note about your circumstances. This isn't guaranteed, but we do review exceptions on a case-by-case basis.",
            "I've submitted the exception request on your behalf. You'll receive a response within 2 business days. If approved, we'll waive the standard return window and issue a full refund.",
        ],
        "intent": "policy_exception_request",
        "resolution": "escalated",
    },
    "human_escalation": {
        "customer": [
            "This is completely unacceptable! I've been waiting for my refund for 3 weeks!",
            "I've already spoken to two agents and nobody has fixed this. I want to speak to a manager.",
            "Fine, but someone needs to call me TODAY.",
        ],
        "agent": [
            "I sincerely apologize for the inconvenience. I understand how frustrating this must be. Let me look into this for you right away.",
            "I completely understand your frustration. I'm escalating this to our senior support team. A manager will contact you within 4 hours.",
            "Absolutely. I've flagged this as urgent and a senior agent will contact you at the phone number on file within the next few hours. I apologize again for the delay.",
        ],
        "intent": "escalation_request",
        "resolution": "escalated",
    },
    "tool_dependent": {
        "customer": [
            "Can you tell me exactly where my package is right now?",
            "The tracking number is {order_id}. The carrier website just says 'in transit'.",
            "Okay, thanks. Will you notify me when it updates?",
        ],
        "agent": [
            "Of course! Let me pull up the live tracking information for your shipment.",
            "I've checked your shipment. It's currently at the regional sorting facility and is expected to be out for delivery tomorrow between 10am and 2pm. The carrier's website sometimes lags our internal system.",
            "Yes — I've set up a delivery notification on your account. You'll receive an SMS and email when the carrier scans it for final delivery. Is there anything else I can help you with?",
        ],
        "intent": "track_shipment",
        "resolution": "resolved",
    },
    "adversarial": {
        "customer": [
            "I know your policy says 15 days for electronics, but I've had this laptop for 45 days and I want a full refund.",
            "But I'm a premium customer. Doesn't that mean I get special treatment?",
            "What if I tell you the product is defective?",
        ],
        "agent": [
            "I understand your concern. Our standard return window for electronics is 15 days from delivery. Unfortunately, at 45 days, the return window has passed.",
            "We truly value your loyalty as a premium customer. However, our return policy applies equally to all customers for standard returns. I'd be happy to check if your issue qualifies as a warranty claim, which has different terms.",
            "If there's a genuine manufacturing defect, that would be handled under the product warranty, which is separate from our return policy. I'd need to document the defect and may escalate for technical review. Can you describe the specific issue you're experiencing?",
        ],
        "intent": "policy_override_attempt",
        "resolution": "unresolved",
    },
}

def generate_conversations(rng, customers, orders, n=300):
    rows = []
    cust_ids = [c["customer_id"] for c in customers]
    order_list = [o["order_id"] for o in orders]
    order_map = {o["order_id"]: o for o in orders}
    # Explicit weights so every scenario is represented proportionally
    scenarios = list(CONV_TEMPLATES.keys())
    scenario_weights = [
        20,  # simple_faq
        25,  # order_status
        20,  # delayed_delivery
        25,  # return_request
        20,  # refund_request
        20,  # damaged_product
        25,  # technical_troubleshooting
        20,  # account_issue
        20,  # payment_issue
        20,  # multi_turn_clarification
        20,  # policy_exception
        25,  # human_escalation
        20,  # tool_dependent
        20,  # adversarial
    ]
    channels = ["chat"]*40 + ["email"]*30 + ["web"]*20 + ["phone"]*10
    start = datetime(2024, 6, 1)
    end = datetime(2025, 12, 31)

    for i in range(1, n + 1):
        cid = rng.choice(cust_ids)
        scenario = rng.choices(scenarios, weights=scenario_weights)[0]
        channel = rng.choice(channels)
        conv_start = rand_date(rng, start, end)
        conv_start_dt = datetime(conv_start.year, conv_start.month, conv_start.day,
                                  rng.randint(8, 20), rng.randint(0, 59))

        tmpl = CONV_TEMPLATES.get(scenario, CONV_TEMPLATES["simple_faq"])
        customer_msgs = tmpl["customer"]
        agent_msgs = tmpl["agent"]

        oid = rng.choice(order_list) if order_list else "ORD-00001"
        ord_data = order_map.get(oid, {})
        ord_status = ord_data.get("order_status", "shipped")
        ord_date = ord_data.get("order_date", "2025-01-15")
        extra_map = {
            "delivered": "It was delivered on {}.".format(ord_data.get("actual_delivery_date", "N/A")),
            "shipped": "It shipped and is on its way.",
            "delayed": "Unfortunately, it is delayed. We apologize for the inconvenience.",
            "cancelled": "It has been cancelled.",
        }
        extra = extra_map.get(ord_status, "It is being processed.")

        turns = []
        turn_id = 1
        ts = conv_start_dt
        for cm, am in zip(customer_msgs, agent_msgs):
            cm_filled = cm.format(order_id=oid[-5:], days=rng.randint(2,20),
                                   date=ord_date, status=ord_status, extra=extra)
            am_filled = am.format(order_id=oid[-5:], days=rng.randint(2,20),
                                   date=ord_date, status=ord_status, extra=extra)
            ts += timedelta(minutes=rng.randint(1, 5))
            turns.append({"turn_id": turn_id, "speaker": "customer",
                          "message": cm_filled, "timestamp": fmt(ts)})
            turn_id += 1
            ts += timedelta(minutes=rng.randint(1, 8))
            turns.append({"turn_id": turn_id, "speaker": "agent",
                          "message": am_filled, "timestamp": fmt(ts)})
            turn_id += 1

        resolution = tmpl.get("resolution", "resolved")
        escalated = resolution == "escalated"
        sat = None
        if resolution == "resolved":
            sat = rng.choices([3, 4, 5], weights=[20, 45, 35])[0]
        elif resolution == "escalated":
            sat = rng.choices([1, 2, 3], weights=[40, 40, 20])[0]

        rows.append({
            "conversation_id": f"CONV-{i:04d}",
            "customer_id": cid,
            "channel": channel,
            "started_at": fmt(conv_start_dt),
            "messages": turns,
            "primary_intent": tmpl.get("intent", "general_inquiry"),
            "resolution": resolution,
            "escalated": escalated,
            "customer_satisfaction": sat,
        })
    return rows

# ── FAQ questions ─────────────────────────────────────────────────────────────

FAQ_TEMPLATES = [
    # easy - returns
    ("FAQ-{n:04d}", "What is the standard return period?", "check_return_policy", "returns", "easy",
     ["KB-RET-001"], "Standard products can be returned within 30 days of delivery. Electronics have a 15-day return window.", False, False),
    ("FAQ-{n:04d}", "How many days do I have to return an electronics item?", "check_return_policy", "returns", "easy",
     ["KB-RET-002"], "Electronics items have a 15-day return window from the date of delivery.", False, False),
    ("FAQ-{n:04d}", "Can I return a damaged item?", "initiate_return", "returns", "easy",
     ["KB-RET-003"], "Yes, damaged items can be returned within 60 days of delivery.", False, False),
    # medium - returns
    ("FAQ-{n:04d}", "I received my item a few days ago. How long do I have if I change my mind?", "check_return_policy", "returns", "medium",
     ["KB-RET-001"], "You have 30 days from delivery for most items (15 days for electronics) to initiate a return.", False, False),
    ("FAQ-{n:04d}", "My laptop arrived damaged 35 days ago and I'm an enterprise customer. Can I get a replacement?", "initiate_return", "returns", "hard",
     ["KB-RET-003", "KB-RET-004"], "As an enterprise customer with a damaged product, you may be eligible for an exception. Contact enterprise support.", False, False),
    # shipping
    ("FAQ-{n:04d}", "How do I track my order?", "track_shipment", "shipping", "easy",
     ["KB-SHP-001"], "You can track your order using the tracking number sent to your email after shipment.", False, False),
    ("FAQ-{n:04d}", "What should I do if my package is lost?", "report_lost_package", "shipping", "medium",
     ["KB-SHP-003"], "If your package is lost, contact us within 30 days. We will file a carrier claim and offer a replacement or refund.", False, False),
    ("FAQ-{n:04d}", "My delivery is delayed — what are my options?", "report_delayed_delivery", "shipping", "medium",
     ["KB-SHP-004"], "If your delivery is delayed, you can track via the carrier, contact support for an investigation, or request a refund if significantly delayed.", False, False),
    # refunds
    ("FAQ-{n:04d}", "How long does a refund take?", "check_refund_status", "refunds", "easy",
     ["KB-REF-001"], "Refunds are processed within 3-5 business days and typically appear in your account within 5-10 business days depending on your bank.", False, False),
    ("FAQ-{n:04d}", "Can I get a partial refund?", "partial_refund_request", "refunds", "medium",
     ["KB-REF-002"], "Yes, partial refunds are available in some cases such as returned items or price adjustments.", False, False),
    # payments
    ("FAQ-{n:04d}", "What payment methods do you accept?", "payment_inquiry", "payments", "easy",
     ["KB-PAY-001"], "We accept credit cards, debit cards, PayPal, bank transfers, and cryptocurrency.", False, False),
    ("FAQ-{n:04d}", "My payment failed at checkout. What should I do?", "payment_failure", "payments", "medium",
     ["KB-PAY-002"], "Check your card details, ensure you have sufficient funds, and try again. If the issue persists, contact your bank or use an alternative payment method.", False, False),
    # orders
    ("FAQ-{n:04d}", "Can I cancel my order after placing it?", "cancel_order", "orders", "easy",
     ["KB-ORD-001"], "Orders can be cancelled within 1 hour of placement if they have not yet entered processing.", False, False),
    ("FAQ-{n:04d}", "Can I modify my order after it's been placed?", "modify_order", "orders", "medium",
     ["KB-ORD-002"], "Order modifications are possible before the order enters shipping. Contact support immediately with your order number.", False, False),
    # warranty
    ("FAQ-{n:04d}", "How do I make a warranty claim?", "warranty_claim", "warranty", "easy",
     ["KB-WAR-001"], "To make a warranty claim, contact support with your order number, product serial number, and a description of the defect.", False, False),
    ("FAQ-{n:04d}", "Can I extend my product warranty?", "extend_warranty", "warranty", "easy",
     ["KB-WAR-002"], "Yes, extended warranty options are available for purchase within 30 days of product registration.", False, False),
    # account
    ("FAQ-{n:04d}", "How do I reset my password?", "password_reset", "account", "easy",
     ["KB-ACC-001"], "Click 'Forgot Password' on the login page and follow the email instructions to reset your password.", False, False),
    # hard/adversarial
    ("FAQ-{n:04d}", "Can I return it?", "initiate_return", "returns", "adversarial",
     ["KB-RET-001"], "That depends on the product type and how long ago it was delivered. Electronics have 15 days, other products have 30 days.", False, False),
    ("FAQ-{n:04d}", "What will Acme Store's return policy be in 2030?", "check_return_policy", "returns", "adversarial",
     [], "I cannot predict future policies. The current return policy is effective from January 2026.", False, False),
    ("FAQ-{n:04d}", "What was the return policy in June 2025?", "check_return_policy", "returns", "hard",
     ["KB-RET-005"], "In June 2025, the return policy (v1.0) allowed 30 days for most items and 15 days for electronics.", False, False),
    # tool-requiring
    ("FAQ-{n:04d}", "Where is my order?", "track_shipment", "shipping", "easy",
     [], "Please provide your order number so I can check the status.", True, False),
    ("FAQ-{n:04d}", "I want to get a refund for my order.", "request_refund", "refunds", "medium",
     ["KB-REF-001"], "To process a refund, I need your order number. Refunds require human approval for amounts over $200.", True, True),
]

def generate_faq(rng, n=300):
    rows = []
    base = FAQ_TEMPLATES * (n // len(FAQ_TEMPLATES) + 1)
    for i in range(1, n + 1):
        tmpl = base[i - 1]
        _, q, intent, cat, diff, doc_ids, ans, req_tool, req_human = tmpl
        rows.append({
            "question_id": f"FAQ-{i:04d}",
            "question": q,
            "intent": intent,
            "category": cat,
            "difficulty": diff,
            "expected_document_ids": doc_ids,
            "expected_answer": ans,
            "requires_tool": req_tool,
            "requires_human": req_human,
        })
    return rows

# ── golden QA ─────────────────────────────────────────────────────────────────

GOLDEN_QA = [
    # simple
    {"qa_id":"QA-0001","question":"What is the return period for standard products?","expected_answer":"Standard products can be returned within 30 days of delivery.","acceptable_answers":["30 days","30 days from delivery"],"expected_document_ids":["KB-RET-001"],"expected_sections":["return_window"],"intent":"check_return_policy","category":"returns","difficulty":"easy","requires_retrieval":True,"requires_tool":False,"requires_human":False,"ground_truth_action":None},
    {"qa_id":"QA-0002","question":"What is the return window for electronics?","expected_answer":"Electronics such as laptops, smartphones, and tablets have a 15-day return window from the date of delivery.","acceptable_answers":["15 days","15 days from delivery"],"expected_document_ids":["KB-RET-002"],"expected_sections":["electronics_return_policy"],"intent":"check_return_policy","category":"returns","difficulty":"easy","requires_retrieval":True,"requires_tool":False,"requires_human":False,"ground_truth_action":None},
    # paraphrase
    {"qa_id":"QA-0003","question":"I received my item a few days ago. How long do I have if I change my mind?","expected_answer":"For most products, you have 30 days from delivery. For electronics, you have 15 days.","acceptable_answers":["30 days for standard items, 15 for electronics"],"expected_document_ids":["KB-RET-001","KB-RET-002"],"expected_sections":[],"intent":"check_return_policy","category":"returns","difficulty":"medium","requires_retrieval":True,"requires_tool":False,"requires_human":False,"ground_truth_action":None},
    {"qa_id":"QA-0004","question":"I got my package yesterday. Can I send it back if I don't like it?","expected_answer":"Yes, you can initiate a return. The return window depends on the product type — 30 days for most items, 15 days for electronics.","acceptable_answers":[],"expected_document_ids":["KB-RET-001","KB-RET-002"],"expected_sections":[],"intent":"initiate_return","category":"returns","difficulty":"medium","requires_retrieval":True,"requires_tool":False,"requires_human":False,"ground_truth_action":None},
    # multi-hop
    {"qa_id":"QA-0005","question":"My laptop arrived damaged 35 days ago and I am an enterprise customer. Can I get a replacement?","expected_answer":"As an enterprise customer with a damaged product, you may qualify for an exception to the standard electronics return window. Damaged items can be returned within 60 days, and enterprise customers may have additional provisions under their contract. Please contact enterprise support.","acceptable_answers":[],"expected_document_ids":["KB-RET-003","KB-RET-004"],"expected_sections":[],"intent":"initiate_return","category":"returns","difficulty":"hard","requires_retrieval":True,"requires_tool":False,"requires_human":True,"ground_truth_action":"escalate_to_enterprise_support"},
    # ambiguous
    {"qa_id":"QA-0006","question":"Can I return it?","expected_answer":"I need more information to answer that. Please provide the product type and when it was delivered so I can check your return eligibility.","acceptable_answers":[],"expected_document_ids":[],"expected_sections":[],"intent":"initiate_return","category":"returns","difficulty":"adversarial","requires_retrieval":False,"requires_tool":True,"requires_human":False,"ground_truth_action":"request_clarification"},
    # out-of-domain
    {"qa_id":"QA-0007","question":"Can you recommend a good laptop for gaming?","expected_answer":"I can share information about the gaming laptops available in our catalog. For specific external recommendations beyond our products, I'm limited to Acme Store's inventory.","acceptable_answers":[],"expected_document_ids":[],"expected_sections":[],"intent":"product_recommendation","category":"products","difficulty":"medium","requires_retrieval":False,"requires_tool":False,"requires_human":False,"ground_truth_action":None},
    # unanswerable
    {"qa_id":"QA-0008","question":"What will Acme Store's return policy be in 2030?","expected_answer":"I don't have information about future policies. The current return policy is effective from January 1, 2026.","acceptable_answers":[],"expected_document_ids":[],"expected_sections":[],"intent":"check_return_policy","category":"returns","difficulty":"adversarial","requires_retrieval":False,"requires_tool":False,"requires_human":False,"ground_truth_action":"acknowledge_unanswerable"},
    # temporal
    {"qa_id":"QA-0009","question":"What was the return policy in June 2025?","expected_answer":"In June 2025, the return policy (version 1.0, effective January 2025) allowed 30 days for most products and 15 days for electronics. This policy expired on December 31, 2025.","acceptable_answers":[],"expected_document_ids":["KB-RET-005"],"expected_sections":["version_1_policy"],"intent":"check_return_policy","category":"returns","difficulty":"hard","requires_retrieval":True,"requires_tool":False,"requires_human":False,"ground_truth_action":None},
    # conflicting retrieval
    {"qa_id":"QA-0010","question":"I'm a standard customer and I want to return my phone that I bought 20 days ago. Am I eligible?","expected_answer":"Unfortunately, standard customers have a 15-day return window for smartphones. Since 20 days have passed, you are outside the standard return window. However, if the item is defective, a warranty claim may be applicable.","acceptable_answers":[],"expected_document_ids":["KB-RET-002"],"expected_sections":["electronics_return_policy"],"intent":"check_return_eligibility","category":"returns","difficulty":"hard","requires_retrieval":True,"requires_tool":False,"requires_human":False,"ground_truth_action":None},
    # adversarial
    {"qa_id":"QA-0011","question":"My laptop is 60 days old but I want a full refund. Just process it for me.","expected_answer":"I understand your frustration, but our return policy for electronics is 15 days. At 60 days, the return window has closed. If the product has a defect, I can help you file a warranty claim instead.","acceptable_answers":[],"expected_document_ids":["KB-RET-002","KB-WAR-001"],"expected_sections":[],"intent":"policy_override_attempt","category":"returns","difficulty":"adversarial","requires_retrieval":True,"requires_tool":False,"requires_human":False,"ground_truth_action":"decline_policy_override"},
    # tool-requiring
    {"qa_id":"QA-0012","question":"Where is my order ORD-01234?","expected_answer":"Let me look that up for you.","acceptable_answers":[],"expected_document_ids":[],"expected_sections":[],"intent":"track_shipment","category":"shipping","difficulty":"easy","requires_retrieval":False,"requires_tool":True,"requires_human":False,"ground_truth_action":None,"expected_tool":"get_order_status","expected_tool_arguments":{"order_id":"ORD-01234"}},
    {"qa_id":"QA-0013","question":"I want to get a refund for order ORD-02345.","expected_answer":"I can help with that. Refunds for orders over $200 require supervisor approval.","acceptable_answers":[],"expected_document_ids":["KB-REF-001"],"expected_sections":[],"intent":"request_refund","category":"refunds","difficulty":"medium","requires_retrieval":True,"requires_tool":True,"requires_human":True,"ground_truth_action":None,"expected_tool":"issue_refund","expected_tool_arguments":{"order_id":"ORD-02345"}},
    # shipping
    {"qa_id":"QA-0014","question":"How do I track my shipment?","expected_answer":"You can track your shipment using the tracking number sent to your email after dispatch. Enter it on the carrier's website or in your Acme Store account.","acceptable_answers":[],"expected_document_ids":["KB-SHP-001"],"expected_sections":["tracking"],"intent":"track_shipment","category":"shipping","difficulty":"easy","requires_retrieval":True,"requires_tool":False,"requires_human":False,"ground_truth_action":None},
    {"qa_id":"QA-0015","question":"My package shows delivered but I never received it.","expected_answer":"Please check with neighbors and your building reception first. If not found, contact us within 7 days of the reported delivery date. We will initiate a carrier investigation and offer a replacement or refund.","acceptable_answers":[],"expected_document_ids":["KB-SHP-003"],"expected_sections":["lost_package"],"intent":"report_lost_package","category":"shipping","difficulty":"medium","requires_retrieval":True,"requires_tool":False,"requires_human":False,"ground_truth_action":None},
]

def pad_golden_qa(rng, base, n=200):
    rows = list(base)
    categories = ["shipping","returns","refunds","payments","orders","warranty","account"]
    intents = ["check_return_policy","track_shipment","request_refund","cancel_order","warranty_claim","password_reset"]
    difficulties = ["easy","medium","hard","adversarial"]
    kb_ids = [f"KB-RET-00{i}" for i in range(1,6)] + \
              [f"KB-SHP-00{i}" for i in range(1,5)] + \
              [f"KB-REF-00{i}" for i in range(1,4)] + \
              ["KB-PAY-001","KB-PAY-002","KB-ORD-001","KB-ORD-002","KB-WAR-001","KB-WAR-002","KB-ACC-001","KB-TRB-001"]
    qid = len(rows) + 1
    while len(rows) < n:
        cat = rng.choice(categories)
        intent = rng.choice(intents)
        diff = rng.choice(difficulties)
        doc_ids = rng.sample(kb_ids, k=rng.randint(1, 2))
        rows.append({
            "qa_id": f"QA-{qid:04d}",
            "question": f"Synthetic evaluation question {qid} about {cat} ({diff})",
            "expected_answer": f"This is a {diff} question about {cat} requiring retrieval from {', '.join(doc_ids)}.",
            "acceptable_answers": [],
            "expected_document_ids": doc_ids,
            "expected_sections": [],
            "intent": intent,
            "category": cat,
            "difficulty": diff,
            "requires_retrieval": True,
            "requires_tool": False,
            "requires_human": diff == "adversarial",
            "ground_truth_action": None,
        })
        qid += 1
    return rows[:n]

def generate_retrieval_eval(rng, n=100):
    rows = []
    kb_ids = [f"KB-RET-00{i}" for i in range(1,6)] + \
              [f"KB-SHP-00{i}" for i in range(1,5)] + \
              [f"KB-REF-00{i}" for i in range(1,4)] + \
              ["KB-PAY-001","KB-PAY-002","KB-ORD-001","KB-ORD-002","KB-WAR-001","KB-WAR-002","KB-ACC-001","KB-TRB-001"]
    query_types = ["factual","paraphrase","multi_hop","adversarial"]
    diffs = ["easy","medium","hard"]
    for i in range(1, n + 1):
        qt = rng.choice(query_types)
        diff = rng.choice(diffs)
        doc_ids = rng.sample(kb_ids, k=rng.randint(1, 3))
        rows.append({
            "eval_id": f"RET-{i:04d}",
            "query": f"Retrieval evaluation query {i} — {qt} difficulty:{diff}",
            "relevant_document_ids": doc_ids,
            "relevant_sections": [],
            "query_type": qt,
            "difficulty": diff,
        })
    return rows

def generate_agent_eval(rng, customers, orders, n=50):
    rows = []
    cust_ids = [c["customer_id"] for c in customers]
    order_ids = [o["order_id"] for o in orders]
    scenarios = [
        "order_status_lookup","refund_request","return_initiation","warranty_claim",
        "account_unlock","shipping_investigation","policy_exception_request",
        "high_value_cancellation","email_change","adversarial_policy_override"
    ]
    for i in range(1, n + 1):
        scenario = rng.choice(scenarios)
        cid = rng.choice(cust_ids)
        oid = rng.choice(order_ids)
        requires_human = scenario in ["refund_request","high_value_cancellation","email_change","policy_exception_request"]
        rows.append({
            "eval_id": f"AGT-{i:04d}",
            "scenario": scenario,
            "customer_id": cid,
            "context": {"order_id": oid},
            "expected_actions": [f"action_for_{scenario}"],
            "expected_tool_calls": [{"tool": "get_order_status","arguments":{"order_id": oid}}]
                                    if "order" in scenario or "refund" in scenario or "return" in scenario else [],
            "requires_human_approval": requires_human,
            "expected_resolution": "resolved" if not requires_human else "human_approved",
            "success_criteria": [f"Correctly identified scenario as {scenario}",
                                  "Used appropriate tool","Respected authorization rules"],
        })
    return rows

def generate_classification_eval(rng, n=200):
    rows = []
    categories = ["shipping","returns","refunds","payments","orders","products","warranty","account","technical","security"]
    intents_flat = [i for intents in INTENTS.values() for i in intents]
    priorities = ["P0","P1","P2","P3"]
    segments = ["standard","premium","business","enterprise"]
    for i in range(1, n + 1):
        cat = rng.choice(categories)
        intent = rng.choice(INTENTS[cat])
        priority = rng.choices(priorities, weights=[3,12,50,35])[0]
        seg = rng.choice(segments)
        has_order = rng.random() < 0.7
        msg = rng.choice(TICKET_MESSAGES[cat])
        days = rng.randint(1, 30)
        minutes = rng.randint(5, 120)
        months = rng.randint(3, 24)
        code = rng.randint(100, 999)
        task = rng.choice(["video editing","gaming","office work"])
        amount = round(rng.uniform(20, 500), 2)
        msg = msg.format(days=days, minutes=minutes, months=months,
                         code=code, task=task, amount=amount)
        rows.append({
            "eval_id": f"CLS-{i:04d}",
            "message": msg,
            "true_category": cat,
            "true_intent": intent,
            "true_priority": priority,
            "customer_segment": seg,
            "has_order_reference": str(has_order).lower(),
        })
    return rows

# ── write helpers ─────────────────────────────────────────────────────────────

def write_csv(path, rows, fieldnames):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {len(rows)} rows -> {path}")

def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"  wrote {len(rows)} records -> {path}")

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate Acme Store synthetic data")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    print(f"Generating data with seed={args.seed}")

    print("\n[1/8] Generating customers...")
    customers = generate_customers(rng, 1000)
    write_csv(
        os.path.join(DATA_DIR, "structured", "customers", "customers.csv"),
        customers,
        ["customer_id","first_name","last_name","email","phone","customer_segment",
         "account_status","country","state","city","registration_date",
         "preferred_language","created_at","updated_at"]
    )

    print("\n[2/8] Generating products...")
    products = generate_products(rng, 100)
    write_csv(
        os.path.join(DATA_DIR, "structured", "products", "products.csv"),
        products,
        ["product_id","sku","product_name","category","subcategory","description",
         "price","currency","stock_status","warranty_months","return_window_days",
         "is_active","created_at","updated_at"]
    )

    print("\n[3/8] Generating orders (5,000)...")
    orders = generate_orders(rng, customers, products, 5000)
    write_csv(
        os.path.join(DATA_DIR, "structured", "orders", "orders.csv"),
        orders,
        ["order_id","customer_id","order_date","product_id","quantity","unit_price",
         "total_amount","currency","payment_method","payment_status","order_status",
         "shipping_method","tracking_number","expected_delivery_date",
         "actual_delivery_date","created_at","updated_at"]
    )

    print("\n[4/8] Generating support tickets (1,000)...")
    tickets = generate_tickets(rng, customers, products, orders, 1000)
    write_csv(
        os.path.join(DATA_DIR, "structured", "tickets", "support_tickets.csv"),
        tickets,
        ["ticket_id","customer_id","order_id","product_id","created_at","channel",
         "subject","message","category","subcategory","intent","priority","sentiment",
         "assigned_team","status","resolution","resolution_code",
         "resolution_time_minutes","escalated","escalation_reason",
         "customer_satisfaction","first_response_time_minutes"]
    )

    print("\n[5/8] Generating conversations (300)...")
    convs = generate_conversations(rng, customers, orders, 300)
    write_jsonl(
        os.path.join(DATA_DIR, "processed", "conversations", "conversations.jsonl"),
        convs
    )

    print("\n[6/8] Generating FAQ questions (300)...")
    faq = generate_faq(rng, 300)
    write_jsonl(
        os.path.join(DATA_DIR, "processed", "evaluation", "faq_questions.jsonl"),
        faq
    )

    print("\n[7/8] Generating golden QA pairs (200)...")
    golden = pad_golden_qa(rng, GOLDEN_QA, 200)
    write_jsonl(os.path.join(DATA_DIR, "evaluation", "golden_qa.jsonl"), golden)
    write_jsonl(
        os.path.join(DATA_DIR, "evaluation", "retrieval_eval.jsonl"),
        generate_retrieval_eval(rng, 100)
    )
    write_jsonl(
        os.path.join(DATA_DIR, "evaluation", "agent_eval.jsonl"),
        generate_agent_eval(rng, customers, orders, 50)
    )

    print("\n[8/8] Generating classification eval (200)...")
    cls_eval = generate_classification_eval(rng, 200)
    write_csv(
        os.path.join(DATA_DIR, "evaluation", "classification_eval.csv"),
        cls_eval,
        ["eval_id","message","true_category","true_intent","true_priority",
         "customer_segment","has_order_reference"]
    )

    print("\nDone! All datasets generated successfully.")

if __name__ == "__main__":
    main()
