"""Initialize the database: run Alembic migrations then seed from CSV files."""
from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import sys
from pathlib import Path

# Ensure repo root is on the path so scripts.seed_db is importable
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run migrations and seed the database.")
    parser.add_argument(
        "--database-url",
        default=None,
        help="Async SQLAlchemy database URL (defaults to DATABASE_URL env var).",
    )
    args = parser.parse_args()

    database_url = args.database_url or os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL is not set.", file=sys.stderr)
        sys.exit(1)

    # -----------------------------------------------------------------------
    # Step 1: run Alembic migrations
    # -----------------------------------------------------------------------
    print("Step 1: Running Alembic migrations...")
    subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=str(REPO_ROOT),
        check=True,
    )
    print("Migrations complete.")

    # -----------------------------------------------------------------------
    # Step 2: seed the database
    # -----------------------------------------------------------------------
    print("Step 2: Seeding the database...")
    from scripts.seed_db import main as seed_main  # noqa: PLC0415

    asyncio.run(seed_main(database_url))
    print("Database initialisation complete.")


if __name__ == "__main__":
    main()
