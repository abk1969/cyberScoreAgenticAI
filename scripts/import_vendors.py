#!/usr/bin/env python3
"""
CyberScore Bulk Vendor Import from CSV.

Imports vendors from a CSV file into the database.
Expected CSV columns: name, domain, tier, service_type, country

Usage:
    python scripts/import_vendors.py --file vendors.csv
    python scripts/import_vendors.py --file vendors.csv --dry-run
"""

import argparse
import asyncio
import csv
import sys
import uuid
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://csadmin:changeme_db_password@localhost:5432/cyberscore"

REQUIRED_COLUMNS = {"name", "domain"}
OPTIONAL_COLUMNS = {"tier", "service_type", "country"}
VALID_TIERS = {"critical", "important", "standard"}


def validate_row(row: dict, line_num: int) -> list[str]:
    """Validate a single CSV row and return list of errors."""
    errors = []

    if not row.get("name", "").strip():
        errors.append(f"Line {line_num}: missing 'name'")
    if not row.get("domain", "").strip():
        errors.append(f"Line {line_num}: missing 'domain'")

    tier = row.get("tier", "standard").strip().lower()
    if tier and tier not in VALID_TIERS:
        errors.append(f"Line {line_num}: invalid tier '{tier}' (must be: {', '.join(VALID_TIERS)})")

    return errors


def parse_csv(file_path: Path) -> tuple[list[dict], list[str]]:
    """Parse and validate CSV file. Returns (rows, errors)."""
    rows = []
    errors = []

    with open(file_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            return [], ["CSV file is empty or has no header row"]

        header_set = set(reader.fieldnames)
        missing = REQUIRED_COLUMNS - header_set
        if missing:
            return [], [f"Missing required columns: {', '.join(missing)}"]

        for i, row in enumerate(reader, start=2):
            row_errors = validate_row(row, i)
            if row_errors:
                errors.extend(row_errors)
            else:
                rows.append({
                    "id": str(uuid.uuid4()),
                    "name": row["name"].strip(),
                    "domain": row["domain"].strip(),
                    "tier": row.get("tier", "standard").strip().lower() or "standard",
                    "service_type": row.get("service_type", "").strip() or "Non spécifié",
                    "country": row.get("country", "").strip() or "France",
                })

    return rows, errors


async def import_vendors(rows: list[dict], dry_run: bool = False) -> tuple[int, int]:
    """Import vendor rows into database. Returns (inserted, skipped)."""
    if dry_run:
        print(f"\n[DRY RUN] Would import {len(rows)} vendors:")
        for row in rows:
            print(f"  - {row['name']} ({row['domain']}) [{row['tier']}]")
        return len(rows), 0

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    inserted = 0
    skipped = 0

    async with async_session() as session:
        async with session.begin():
            for row in rows:
                # Check if vendor with same domain already exists
                result = await session.execute(
                    text("SELECT id FROM vendors WHERE domain = :domain"),
                    {"domain": row["domain"]},
                )
                existing = result.fetchone()

                if existing:
                    print(f"  SKIP: {row['name']} ({row['domain']}) - already exists")
                    skipped += 1
                    continue

                await session.execute(
                    text("""
                        INSERT INTO vendors (id, name, domain, tier, service_type, country, created_at, updated_at)
                        VALUES (:id, :name, :domain, :tier, :service_type, :country, NOW(), NOW())
                    """),
                    row,
                )
                print(f"  ADD: {row['name']} ({row['domain']}) [{row['tier']}]")
                inserted += 1

        await session.commit()

    await engine.dispose()
    return inserted, skipped


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CyberScore Bulk Vendor Import",
        epilog="CSV must have columns: name, domain. Optional: tier, service_type, country",
    )
    parser.add_argument(
        "--file", "-f",
        type=Path,
        required=True,
        help="Path to CSV file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and preview without inserting",
    )

    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: File not found: {args.file}")
        sys.exit(1)

    print("CyberScore Vendor Import")
    print("=" * 40)
    print(f"File: {args.file}")

    rows, errors = parse_csv(args.file)

    if errors:
        print(f"\nValidation errors ({len(errors)}):")
        for err in errors:
            print(f"  - {err}")
        if not rows:
            print("\nNo valid rows to import. Aborting.")
            sys.exit(1)
        print(f"\n{len(rows)} valid rows found despite errors. Continuing with valid rows...")

    print(f"\nParsed {len(rows)} vendors from CSV")

    inserted, skipped = asyncio.run(import_vendors(rows, dry_run=args.dry_run))

    print("=" * 40)
    if args.dry_run:
        print(f"[DRY RUN] {inserted} vendors would be imported")
    else:
        print(f"Import complete: {inserted} inserted, {skipped} skipped")


if __name__ == "__main__":
    main()
