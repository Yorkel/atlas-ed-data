# Merges per-source Ireland CSVs into one inference-ready dataset.
#
# Usage:
#   python merge.py                    → outputs ireland_inference.csv
#   python merge.py --output out.csv   → custom output path

import argparse
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IRE_DIR = ROOT / "data" / "training" / "ireland"
INFERENCE_DIR = ROOT / "data" / "inference" / "ireland"

SOURCES = {
    "gov_ie": {
        "file": IRE_DIR / "gov_ie.csv",
        "type": "government",
        "institution_name": "Department of Education (Ireland)",
    },
    "esri": {
        "file": IRE_DIR / "esri.csv",
        "type": "think_tank",
        "institution_name": "ESRI",
    },
    "tasc": {
        "file": IRE_DIR / "tasc.csv",
        "type": "think_tank",
        "institution_name": "TASC",
    },
    "erc": {
        "file": IRE_DIR / "erc.csv",
        "type": "ed_res_org",
        "institution_name": "Educational Research Centre",
    },
    "teaching_council": {
        "file": IRE_DIR / "teaching_council.csv",
        "type": "prof_body",
        "institution_name": "Teaching Council",
    },
    "education_matters": {
        "file": IRE_DIR / "education_matters.csv",
        "type": "ed_journalism",
        "institution_name": "Education Matters",
    },
    "irish_times": {
        "file": IRE_DIR / "irish_times.csv",
        "type": "ed_journalism",
        "institution_name": "Irish Times Education",
    },
    "ncse": {
        "file": IRE_DIR / "ncse.csv",
        "type": "ed_res_org",
        "institution_name": "NCSE",
    },
    "childrens_rights": {
        "file": IRE_DIR / "childrens_rights.csv",
        "type": "advocacy",
        "institution_name": "Children's Rights Alliance",
    },
}

FINAL_COLS = ["url", "title", "date", "text", "source", "country", "type", "institution_name"]


def load_source(source, config):
    df = pd.read_csv(config["file"])
    df["source"] = source
    df["country"] = "ire"
    df["type"] = config["type"]
    df["institution_name"] = config["institution_name"]

    df = df.dropna(subset=["text"])
    df = df[df["text"].str.strip() != ""]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df[FINAL_COLS]


def parse_args():
    parser = argparse.ArgumentParser(description="Merge Ireland inference CSVs")
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

    out = Path(args.output) if args.output else INFERENCE_DIR / "ireland_inference.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    full.to_csv(out, index=False)

    print(f"\n  Wrote {len(full)} rows to {out}")
    print(full["source"].value_counts().to_string())


if __name__ == "__main__":
    main()
