# Merges per-source Scotland CSVs into one inference-ready dataset.
#
# Usage:
#   python merge.py                    → outputs scotland_inference.csv
#   python merge.py --output out.csv   → custom output path

import argparse
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCOT_DIR = ROOT / "data" / "training" / "scotland"
INFERENCE_DIR = ROOT / "data" / "inference" / "scotland"

SOURCES = {
    "gov_scot": {
        "file": SCOT_DIR / "gov_scot.csv",
        "type": "government",
        "institution_name": "Scottish Government",
    },
    "audit_scotland": {
        "file": SCOT_DIR / "audit_scotland.csv",
        "type": "ed_res_org",
        "institution_name": "Audit Scotland",
    },
    "sera": {
        "file": SCOT_DIR / "sera.csv",
        "type": "think_tank",
        "institution_name": "SERA",
    },
    "gtcs": {
        "file": SCOT_DIR / "gtcs.csv",
        "type": "prof_body",
        "institution_name": "GTCS",
    },
    "tes_scotland": {
        "file": SCOT_DIR / "tes_scotland.csv",
        "type": "ed_journalism",
        "institution_name": "TES Scotland",
    },
    "education_scotland": {
        "file": SCOT_DIR / "education_scotland.csv",
        "type": "gov_agency",
        "institution_name": "Education Scotland",
    },
}

FINAL_COLS = ["url", "title", "date", "text", "source", "country", "type", "institution_name"]


def load_source(source, config):
    df = pd.read_csv(config["file"])
    df["source"] = source
    df["country"] = "sco"
    df["type"] = config["type"]
    df["institution_name"] = config["institution_name"]

    df = df.dropna(subset=["text"])
    df = df[df["text"].str.strip() != ""]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df[FINAL_COLS]


def parse_args():
    parser = argparse.ArgumentParser(description="Merge Scotland inference CSVs")
    parser.add_argument("--output", type=str, default=None, help="Custom output path")
    return parser.parse_args()


def main():
    args = parse_args()
    frames = []

    for source, config in SOURCES.items():
        if not config["file"].exists():
            print(f"  Missing: {config['file'].name} — skipping")
            continue
        df = load_source(source, config)
        print(f"  {source}: {len(df)} rows")
        frames.append(df)

    if not frames:
        print("  No source files found. Exiting.")
        return

    full = pd.concat(frames, ignore_index=True)
    full["date"] = pd.to_datetime(full["date"], errors="coerce")

    # Drop duplicate URLs
    before = len(full)
    full = full.drop_duplicates(subset=["url"])
    dupes = before - len(full)
    if dupes:
        print(f"  Dropped {dupes} duplicate rows")

    out = Path(args.output) if args.output else INFERENCE_DIR / "scotland_inference.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    full.to_csv(out, index=False)

    print(f"\n  Wrote {len(full)} rows to {out}")
    print(full["source"].value_counts().to_string())


if __name__ == "__main__":
    main()
