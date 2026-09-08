"""Seed the database from CSV files in data/structured/."""
from __future__ import annotations

import argparse
import asyncio
import csv
import os
import sys
import uuid
from decimal import Decimal
from pathlib import Path

import dateutil.parser
from passlib.context import CryptContext
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ---------------------------------------------------------------------------
# Ensure src/ is on the path so we can import app models directly
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app.models.customer import Customer  # noqa: E402
from app.models.order import Order, OrderItem  # noqa: E402
from app.models.product import Product  # noqa: E402
from app.models.ticket import SupportTicket  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DATA_DIR = REPO_ROOT / "data" / "structured"
BATCH_SIZE = 500

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
HASHED_PASSWORD = _pwd_ctx.hash("TestPassword123!")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uid(str_id: str) -> uuid.UUID:
    """Deterministic UUID from a CSV string ID."""
    return uuid.uuid5(uuid.NAMESPACE_DNS, str_id)


def _parse_dt(value: str):
    """Parse an ISO date string; return None for empty / invalid strings."""
    if not value or not value.strip():
        return None
    try:
        return dateutil.parser.parse(value)
    except Exception:
        return None


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------

async def _seed_products(session: AsyncSession) -> None:
    existing = await session.scalar(select(func.count()).select_from(Product))
    if existing:
        print(f"  products table already has {existing} rows — skipping.")
        return

    rows = _read_csv(DATA_DIR / "products" / "products.csv")
    print(f"Seeding {len(rows)} products...", end=" ", flush=True)

    batch: list[Product] = []
    for row in rows:
        batch.append(
            Product(
                id=_uid(row["product_id"]),
                sku=row["sku"],
                name=row["product_name"],
                category=row["category"],
                subcategory=row["subcategory"] or None,
                price=Decimal(row["price"]),
                warranty_months=int(row["warranty_months"]),
                is_active=row["is_active"].strip().lower() == "true",
            )
        )
        if len(batch) >= BATCH_SIZE:
            session.add_all(batch)
            await session.flush()
            batch.clear()

    if batch:
        session.add_all(batch)
        await session.flush()

    print("done.")


async def _seed_customers(session: AsyncSession) -> None:
    existing = await session.scalar(select(func.count()).select_from(Customer))
    if existing:
        print(f"  customers table already has {existing} rows — skipping.")
        return

    rows = _read_csv(DATA_DIR / "customers" / "customers.csv")
    print(f"Seeding {len(rows)} customers...", end=" ", flush=True)

    batch: list[Customer] = []
    for row in rows:
        phone = row.get("phone", "").strip() or None
        batch.append(
            Customer(
                id=_uid(row["customer_id"]),
                email=row["email"],
                name=f"{row['first_name']} {row['last_name']}",
                phone=phone,
                city=row.get("city") or None,
                state=row.get("state") or None,
                country=row.get("country") or None,
                customer_segment=row.get("customer_segment") or None,
                account_status=row.get("account_status", "active"),
                hashed_password=HASHED_PASSWORD,
            )
        )
        if len(batch) >= BATCH_SIZE:
            session.add_all(batch)
            await session.flush()
            batch.clear()

    if batch:
        session.add_all(batch)
        await session.flush()

    print("done.")


async def _seed_orders(session: AsyncSession) -> None:
    existing = await session.scalar(select(func.count()).select_from(Order))
    if existing:
        print(f"  orders table already has {existing} rows — skipping.")
        return

    rows = _read_csv(DATA_DIR / "orders" / "orders.csv")
    print(f"Seeding {len(rows)} orders + order items...", end=" ", flush=True)

    status_map = {
        "processing": "processing",
        "delivered": "delivered",
        "shipped": "shipped",
        "placed": "pending",
        "cancelled": "cancelled",
        "returned": "refunded",
    }

    order_batch: list[Order] = []
    item_batch: list[OrderItem] = []

    for row in rows:
        raw_status = row["order_status"].strip().lower()
        status = status_map.get(raw_status, raw_status)

        tracking = row.get("tracking_number", "").strip() or None
        carrier = row.get("shipping_method", "").strip() or None

        delivered_at = (
            _parse_dt(row.get("actual_delivery_date", ""))
            if status == "delivered"
            else None
        )
        shipped_at = (
            _parse_dt(row.get("actual_delivery_date", ""))
            if status == "shipped"
            else None
        )

        order_id = _uid(row["order_id"])
        customer_id = _uid(row["customer_id"])
        product_id = _uid(row["product_id"])

        order_batch.append(
            Order(
                id=order_id,
                order_number=row["order_id"],
                customer_id=customer_id,
                status=status,
                total_amount=Decimal(row["total_amount"]),
                currency=row["currency"],
                tracking_number=tracking,
                carrier=carrier,
                shipped_at=shipped_at,
                delivered_at=delivered_at,
            )
        )
        item_batch.append(
            OrderItem(
                id=_uid(row["order_id"] + "_item"),
                order_id=order_id,
                product_id=product_id,
                quantity=int(row["quantity"]),
                unit_price=Decimal(row["unit_price"]),
                total_price=Decimal(row["total_amount"]),
            )
        )

        if len(order_batch) >= BATCH_SIZE:
            session.add_all(order_batch)
            await session.flush()
            session.add_all(item_batch)
            await session.flush()
            order_batch.clear()
            item_batch.clear()

    if order_batch:
        session.add_all(order_batch)
        await session.flush()
        session.add_all(item_batch)
        await session.flush()

    print("done.")


async def _seed_tickets(session: AsyncSession, known_customer_ids: set) -> None:
    existing = await session.scalar(select(func.count()).select_from(SupportTicket))
    if existing:
        print(f"  support_tickets table already has {existing} rows — skipping.")
        return

    rows = _read_csv(DATA_DIR / "tickets" / "support_tickets.csv")
    print(f"Seeding {len(rows)} tickets...", end=" ", flush=True)

    status_map = {
        "closed": "closed",
        "resolved": "resolved",
    }

    batch: list[SupportTicket] = []
    skipped = 0
    for row in rows:
        cid = _uid(row["customer_id"])
        if cid not in known_customer_ids:
            skipped += 1
            continue

        raw_status = row["status"].strip().lower()
        status = status_map.get(raw_status, "open")

        escalated = row.get("escalated", "").strip().lower() == "true"
        escalation_reason = row.get("escalation_reason", "").strip() or None
        if not escalated:
            escalation_reason = None

        assigned_queue = row.get("assigned_team", "").strip() or None

        batch.append(
            SupportTicket(
                id=_uid(row["ticket_id"]),
                ticket_number=row["ticket_id"],
                customer_id=cid,
                category=row["category"],
                priority=row["priority"],
                status=status,
                escalation_reason=escalation_reason,
                assigned_queue=assigned_queue,
            )
        )

        if len(batch) >= BATCH_SIZE:
            session.add_all(batch)
            await session.flush()
            batch.clear()

    if batch:
        session.add_all(batch)
        await session.flush()

    if skipped:
        print(f"done. (skipped {skipped} tickets with unknown customer_id)")
    else:
        print("done.")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def main(database_url: str | None = None) -> None:
    if database_url is None:
        database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL is not set.", file=sys.stderr)
        sys.exit(1)

    engine = create_async_engine(database_url, echo=False, future=True)
    session_factory = async_sessionmaker(
        bind=engine, expire_on_commit=False, autoflush=False, autocommit=False
    )

    async with session_factory() as session:
        await _seed_products(session)
        await _seed_customers(session)

        # Build known customer ID set for FK safety check on tickets
        result = await session.execute(select(Customer.id))
        known_customer_ids: set = {row[0] for row in result.fetchall()}

        await _seed_orders(session)
        await _seed_tickets(session, known_customer_ids)

        await session.commit()

    await engine.dispose()
    print("All done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the database from CSV files.")
    parser.add_argument(
        "--database-url",
        default=None,
        help="Async SQLAlchemy database URL (defaults to DATABASE_URL env var).",
    )
    args = parser.parse_args()
    asyncio.run(main(args.database_url))
