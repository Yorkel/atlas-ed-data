"""
seed_supabase.py
----------------
Upserts articles into the Supabase `articles` table.

Supports two sources:
  - inference  (default): weekly CSVs from data/inference/england/
  - training:             merged CSV at data/training/training_data_v1.csv

Usage (from project root):
    python src/seed_supabase.py                              # seed all inference weeks
    python src/seed_supabase.py --source training            # seed training data
    python src/seed_supabase.py --source all                 # seed both
    python src/seed_supabase.py --week 1                     # seed one inference week
    python src/seed_supabase.py --dry-run                    # print counts without writing

Credentials are read from .env:
    SUPABASE_URL=https://...supabase.co
    SUPABASE_SERVICE_KEY=sb_secret_...

Columns populated at seed time:
    url, dataset_type, title, date, text, source, country, type,
    institution_name, week_number, week_start, week_end,
    preview, election_period

Columns populated later (model / sentiment pipeline):
    topic_num, dominant_topic, dominant_topic_weight,
    topic_probabilities, text_clean, run_id,
    sentiment_score, sentiment_label, contestability_score
"""

import argparse
import os
import re
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).resolve().parent.parent
INFERENCE_DIR = ROOT / "data" / "inference" / "england"
TRAINING_CSV = ROOT / "data" / "training" / "training_data_v1.csv"

# Filename pattern: weekNN_YYYY-MM-DD.csv
FILENAME_RE = re.compile(r"^week(\d+)_(\d{4}-\d{2}-\d{2})\.csv$")

# UK General Election — used to split election_period
UK_GE_2024 = date(2024, 7, 4)

PREVIEW_LENGTH = 300


def get_client():
    load_dotenv(ROOT / ".env")
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    return create_client(url, key)


def parse_filename(filename: str):
    """Extract week_number, week_start, week_end from weekNN_YYYY-MM-DD.csv."""
    m = FILENAME_RE.match(filename)
    if not m:
        return None, None, None
    week_number = int(m.group(1))
    week_end = date.fromisoformat(m.group(2))
    week_start = week_end - timedelta(days=6)
    return week_number, week_start, week_end


def make_preview(text) -> str | None:
    """Return first PREVIEW_LENGTH characters of text, stripped."""
    if not text:
        return None
    return str(text).strip()[:PREVIEW_LENGTH]


def make_election_period(date_str) -> str | None:
    """Return 'pre_election' or 'post_election' relative to 2024 UK General Election."""
    if not date_str:
        return None
    try:
        d = date.fromisoformat(str(date_str)[:10])
        return "post_election" if d >= UK_GE_2024 else "pre_election"
    except (ValueError, TypeError):
        return None


def seed_inference(client, csv_path: Path, dry_run: bool = False):
    """Upsert one inference week CSV into Supabase."""
    filename = csv_path.name
    week_number, week_start, week_end = parse_filename(filename)
    if week_number is None:
        print(f"⚠️  Skipping {filename} — filename doesn't match weekNN_YYYY-MM-DD.csv")
        return 0

    df = pd.read_csv(csv_path)
    df = df.where(pd.notna(df), None)

    records = []
    for _, row in df.iterrows():
        record = {
            "url":              row.get("url"),
            "dataset_type":     "inference",
            "title":            row.get("title"),
            "article_date":     str(row["date"]) if row.get("date") else None,
            "article_text":     row.get("text"),
            "source":           row.get("source"),
            "country":          row.get("country"),
            "article_type":     row.get("type"),
            "institution_name": row.get("institution_name"),
            "week_number":      week_number,
            "week_start":       str(week_start),
            "week_end":         str(week_end),
            "preview":          make_preview(row.get("text")),
            "election_period":  make_election_period(row.get("date")),
        }
        if record["url"]:
            records.append(record)

    if not records:
        print(f"⚠️  {filename}: no valid rows (all missing url)")
        return 0

    if dry_run:
        print(f"[dry-run] {filename}: would upsert {len(records)} rows "
              f"(week {week_number}, {week_start} → {week_end})")
        return len(records)

    client.table("articles").upsert(records, on_conflict="url").execute()
    print(f"✅ {filename}: upserted {len(records)} rows "
          f"(week {week_number}, {week_start} → {week_end})")
    return len(records)


def seed_training(client, dry_run: bool = False):
    """Upsert training_data_v1.csv into Supabase."""
    if not TRAINING_CSV.exists():
        print(f"⚠️  Training CSV not found: {TRAINING_CSV}")
        return 0

    df = pd.read_csv(TRAINING_CSV)
    df = df.where(pd.notna(df), None)

    # Training CSV columns: url, title, date, text, source, type
    # country and institution_name are not in this CSV
    records = []
    for _, row in df.iterrows():
        record = {
            "url":              row.get("url"),
            "dataset_type":     "training",
            "title":            row.get("title"),
            "article_date":     str(row["date"]) if row.get("date") else None,
            "article_text":     row.get("text"),
            "source":           row.get("source"),
            "country":          "england",
            "article_type":     row.get("type"),
            "institution_name": None,
            "preview":          make_preview(row.get("text")),
            "election_period":  make_election_period(row.get("date")),
        }
        if record["url"]:
            records.append(record)

    if not records:
        print("⚠️  training_data_v1.csv: no valid rows (all missing url)")
        return 0

    if dry_run:
        print(f"[dry-run] training_data_v1.csv: would upsert {len(records)} rows")
        return len(records)

    # Upsert in batches of 500 to avoid request size limits
    batch_size = 500
    total = 0
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        client.table("articles").upsert(batch, on_conflict="url").execute()
        total += len(batch)
        print(f"  ↳ batch {i // batch_size + 1}: {total}/{len(records)} rows upserted")

    print(f"✅ training_data_v1.csv: upserted {total} rows")
    return total


def main():
    parser = argparse.ArgumentParser(description="Seed Supabase articles table")
    parser.add_argument(
        "--source",
        choices=["inference", "training", "all"],
        default="inference",
        help="Which data to seed (default: inference)",
    )
    parser.add_argument("--week", type=int, default=None,
                        help="Only seed this inference week number (ignored for training)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be inserted without writing")
    args = parser.parse_args()

    client = None if args.dry_run else get_client()
    total = 0

    if args.source in ("inference", "all"):
        csv_files = sorted(INFERENCE_DIR.glob("week*.csv"))
        if not csv_files:
            print(f"No week*.csv files found in {INFERENCE_DIR}")
        else:
            if args.week is not None:
                csv_files = [f for f in csv_files if parse_filename(f.name)[0] == args.week]
                if not csv_files:
                    print(f"No file found for week {args.week}")
            for csv_path in csv_files:
                total += seed_inference(client, csv_path, dry_run=args.dry_run)

    if args.source in ("training", "all"):
        total += seed_training(client, dry_run=args.dry_run)

    label = "[dry-run] " if args.dry_run else ""
    verb = "would be upserted" if args.dry_run else "upserted"
    print(f"\n{label}Total: {total} rows {verb}")


if __name__ == "__main__":
    main()
