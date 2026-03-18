"""
seed_supabase.py
----------------
Upserts articles into the Supabase `articles_raw` table.

Supports seeding from all three countries:
  - England training data
  - England, Ireland, Scotland inference (retro + weekly)

Usage (from project root):
    python src/seed_supabase.py                          # seed everything
    python src/seed_supabase.py --country eng             # seed England only
    python src/seed_supabase.py --country irl --week 3    # seed Ireland week 3
    python src/seed_supabase.py --dry-run                 # print counts without writing

Credentials are read from .env:
    SUPABASE_URL=https://...supabase.co
    SUPABASE_SERVICE_KEY=sb_secret_...
"""

import argparse
import os
import re
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).resolve().parent.parent

# Data paths
TRAINING_CSV = ROOT / "data" / "training" / "england" / "training_data_v1.csv"
INFERENCE_DIRS = {
    "eng": ROOT / "data" / "inference" / "england",
    "irl": ROOT / "data" / "inference" / "ireland",
    "sco": ROOT / "data" / "inference" / "scotland",
}

COUNTRY_MAP = {"eng": "eng", "irl": "irl", "sco": "sco"}

# Filename patterns
WEEK_RE = re.compile(r"^week(\d+)_(\d{4}-\d{2}-\d{2})\.csv$")
RETRO_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.csv$")

BATCH_SIZE = 500


def get_client():
    load_dotenv(ROOT / ".env")
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    return create_client(url, key)


def csv_to_records(csv_path: Path, dataset_type: str, country: str, week_number=None):
    """Convert a CSV file to a list of Supabase-ready records."""
    df = pd.read_csv(csv_path)
    df = df.where(pd.notna(df), None)

    records = []
    for _, row in df.iterrows():
        record = {
            "url":              row.get("url"),
            "title":            row.get("title"),
            "article_date":     str(row["date"]) if row.get("date") else None,
            "text":             row.get("text"),
            "source":           row.get("source"),
            "country":          country,
            "type":             row.get("type"),
            "institution_name": row.get("institution_name"),
            "language":         row.get("language", "en"),
            "dataset_type":     dataset_type,
            "week_number":      week_number,
        }
        if record["url"]:
            records.append(record)
    return records


def upsert_batch(client, records, label: str, dry_run: bool = False):
    """Upsert records to articles_raw in batches."""
    if not records:
        print(f"⚠️  {label}: no valid rows")
        return 0

    if dry_run:
        print(f"[dry-run] {label}: would upsert {len(records)} rows")
        return len(records)

    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        client.table("articles_raw").upsert(batch, on_conflict="url").execute()
        total += len(batch)
        if len(records) > BATCH_SIZE:
            print(f"  ↳ batch {i // BATCH_SIZE + 1}: {total}/{len(records)}")

    print(f"✅ {label}: upserted {total} rows")
    return total


def seed_training(client, dry_run: bool = False):
    """Seed England training data."""
    if not TRAINING_CSV.exists():
        print(f"⚠️  Training CSV not found: {TRAINING_CSV}")
        return 0

    records = csv_to_records(TRAINING_CSV, "training", "eng", week_number=None)
    return upsert_batch(client, records, "England training", dry_run)


def seed_inference(client, country: str, week_filter=None, dry_run: bool = False):
    """Seed inference data for one country (retro + weekly)."""
    inf_dir = INFERENCE_DIRS.get(country)
    if not inf_dir or not inf_dir.exists():
        print(f"⚠️  No inference directory for {country}")
        return 0

    total = 0

    for csv_path in sorted(inf_dir.glob("*.csv")):
        filename = csv_path.name

        # Weekly file
        m = WEEK_RE.match(filename)
        if m:
            week_num = int(m.group(1))
            if week_filter is not None and week_num != week_filter:
                continue
            records = csv_to_records(csv_path, "inference", country, week_number=week_num)
            total += upsert_batch(client, records, f"{country} week {week_num}", dry_run)
            continue

        # Retro file (e.g. 2025-12-31.csv)
        m = RETRO_RE.match(filename)
        if m:
            if week_filter is not None:
                continue  # skip retro when filtering by week
            records = csv_to_records(csv_path, "inference", country, week_number=None)
            total += upsert_batch(client, records, f"{country} retro ({filename})", dry_run)
            continue

    return total


def main():
    parser = argparse.ArgumentParser(description="Seed Supabase articles_raw table")
    parser.add_argument(
        "--country",
        choices=["eng", "irl", "sco", "all"],
        default="all",
        help="Which country to seed (default: all)",
    )
    parser.add_argument("--week", type=int, default=None,
                        help="Only seed this week number (skips retro)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be inserted without writing")
    args = parser.parse_args()

    client = None if args.dry_run else get_client()
    total = 0

    countries = ["eng", "irl", "sco"] if args.country == "all" else [args.country]

    for country in countries:
        # Training data (England only)
        if country == "eng" and args.week is None:
            total += seed_training(client, dry_run=args.dry_run)

        # Inference data
        total += seed_inference(client, country, week_filter=args.week, dry_run=args.dry_run)

    label = "[dry-run] " if args.dry_run else ""
    print(f"\n{label}Total: {total} rows upserted to articles_raw")


if __name__ == "__main__":
    main()
