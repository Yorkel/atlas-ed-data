# Merges per-source Ireland CSVs into one inference-ready dataset.
#
# Post-processing steps applied:
#   1. Fix gov.ie migration dates (2025-04-11/12) → real dates from article pages
#   2. Filter for primary & secondary education (exclude higher ed / vocational)
#   3. Flag Irish language articles
#   4. Drop empty text, deduplicate
#
# Usage:
#   python merge.py                    → outputs ireland_inference.csv
#   python merge.py --output out.csv   → custom output path

import argparse
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import time
from datetime import datetime

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
    "thejournal": {
        "file": IRE_DIR / "thejournal.csv",
        "type": "ed_journalism",
        "institution_name": "TheJournal.ie",
    },
    "rte": {
        "file": IRE_DIR / "rte.csv",
        "type": "ed_journalism",
        "institution_name": "RTÉ News",
    },
}

FINAL_COLS = ["url", "title", "date", "text", "source", "country", "type", "institution_name", "language"]


# ----------------------------------------------------------
# Post-processing: fix gov.ie migration dates
# ----------------------------------------------------------
GOV_IE_MIGRATION_DATES = {"2025-04-11", "2025-04-12", "2025-04-15", "2025-04-16"}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def fix_gov_ie_dates(df):
    """For gov.ie rows with migration dates, fetch the real 'Published on:' date from the article page."""
    mask = (df["source"] == "gov_ie") & (df["date"].astype(str).str[:10].isin(GOV_IE_MIGRATION_DATES))
    n = mask.sum()
    if n == 0:
        return df

    print(f"\n  Fixing {n} gov.ie migration dates...")
    fixed = 0
    for idx in df[mask].index:
        url = df.at[idx, "url"]
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            soup = BeautifulSoup(r.text, "lxml")
            for li in soup.find_all("li"):
                text = li.get_text(strip=True)
                m = re.match(r"Published on:\s*(\d{1,2}\s+\w+\s+\d{4})", text)
                if m:
                    real_date = datetime.strptime(m.group(1), "%d %B %Y").date()
                    df.at[idx, "date"] = pd.Timestamp(real_date)
                    fixed += 1
                    break
            time.sleep(0.3)
        except Exception as e:
            print(f"    Failed to fix date for {url}: {e}")

    print(f"  Fixed {fixed}/{n} dates")
    return df


# ----------------------------------------------------------
# Post-processing: filter primary & secondary education
# ----------------------------------------------------------
# Score-based filtering: school signals add points, HE signals subtract.
# Title matches weighted x2. Threshold = 2.
#
# This avoids the brittleness of rule-based filters where one mention
# of "college" in body text kills an otherwise school-focused article.

STRONG_SCHOOL = [  # +3
    "leaving cert", "junior cycle", "senior cycle", "transition year",
    "deis", " sna ", " snas ", "sna allocation", "special needs assistant",
    "national school", "post-primary", "special school",
    "junior cert", "school meals", "school transport", "school building",
    "primary curriculum", "board of management", "patron",
    "school secretary", "school staff", "school closure",
]

MEDIUM_SCHOOL = [  # +2
    "school", "schools", "teacher", "teachers", "pupil", "pupils",
    "principal", "classroom", "inspectorate", "enrolment",
]

WEAK_SCHOOL = [  # +1
    "education minister", "department of education", "curriculum",
    "students", "education policy", "education budget",
]

STRONG_UNI = [  # -3
    "phd", "doctoral", "undergraduate", "postgraduate",
    "research grant", "lecture hall", "campus", "tuition fees",
    "university ranking",
]

MEDIUM_UNI = [  # -2
    "university", "universities", "college", "colleges",
    "lecturer", "lecturers", "degree programme", "masters",
    "bachelor",
]

WEAK_UNI = [  # -1
    "semester", "faculty", "academic staff",
]

SCORE_THRESHOLD = 2


def _education_score(title, text):
    """Score an article for primary/secondary relevance. Title matches weighted x2."""
    score = 0

    for source, terms, weight in [
        (title, STRONG_SCHOOL, 3 * 2),  # title x2
        (text,  STRONG_SCHOOL, 3),
        (title, MEDIUM_SCHOOL, 2 * 2),
        (text,  MEDIUM_SCHOOL, 2),
        (title, WEAK_SCHOOL,   1 * 2),
        (text,  WEAK_SCHOOL,   1),
        (title, STRONG_UNI,   -3 * 2),
        (text,  STRONG_UNI,   -3),
        (title, MEDIUM_UNI,   -2 * 2),
        (text,  MEDIUM_UNI,   -2),
        (title, WEAK_UNI,     -1 * 2),
        (text,  WEAK_UNI,     -1),
    ]:
        for term in terms:
            if term in source:
                score += weight

    return score


def filter_primary_secondary(df):
    """Remove articles about higher ed / vocational using score-based filtering."""
    before = len(df)

    def get_score(row):
        title = str(row.get("title", "")).lower()
        text = str(row.get("text", "")).lower()
        return _education_score(title, text)

    df = df.copy()
    df["_ed_score"] = df.apply(get_score, axis=1)

    kept = df[df["_ed_score"] >= SCORE_THRESHOLD].copy()
    removed = before - len(kept)

    # Log some examples of what was removed
    removed_df = df[df["_ed_score"] < SCORE_THRESHOLD]
    if len(removed_df) > 0:
        print(f"  Sample removals (score < {SCORE_THRESHOLD}):")
        for _, row in removed_df.head(5).iterrows():
            print(f"    score={row['_ed_score']:+d} | {row.get('source','')} | {str(row.get('title',''))[:60]}")

    kept = kept.drop(columns=["_ed_score"])
    print(f"  Filtered higher ed/vocational: removed {removed} articles ({before} → {len(kept)})")
    return kept


# ----------------------------------------------------------
# Post-processing: flag non-English language articles
# ----------------------------------------------------------
# Uses langdetect library — works for Irish (ga), Scots Gaelic (gd),
# Welsh (cy), and 50+ other languages. Future-proof for expansion.
from langdetect import detect as _langdetect
from langdetect import LangDetectException


def flag_language(df):
    """Add a 'language' column using langdetect. Defaults to 'en' if detection fails."""
    def detect_language(row):
        text = str(row.get("text", ""))
        if len(text) < 50:
            return "en"
        try:
            return _langdetect(text)
        except LangDetectException:
            return "en"

    df["language"] = df.apply(detect_language, axis=1)
    non_en = df[df["language"] != "en"]
    if len(non_en) > 0:
        print(f"  Non-English articles detected:")
        print(f"    {non_en['language'].value_counts().to_string()}")
    else:
        print(f"  All articles detected as English")
    return df


# ----------------------------------------------------------
# Load + merge
# ----------------------------------------------------------
def load_source(source, config):
    df = pd.read_csv(config["file"])
    df["source"] = source
    df["country"] = "ire"
    df["type"] = config["type"]
    df["institution_name"] = config["institution_name"]

    df = df.dropna(subset=["text"])
    df = df[df["text"].str.strip() != ""]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def parse_args():
    parser = argparse.ArgumentParser(description="Merge Ireland inference CSVs")
    parser.add_argument("--output", type=str, default=None, help="Custom output path")
    parser.add_argument("--skip-date-fix", action="store_true", help="Skip fixing gov.ie migration dates (slow)")
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
    print(f"\n  Total before post-processing: {len(full)}")

    # 1. Fix gov.ie migration dates
    if not args.skip_date_fix:
        full = fix_gov_ie_dates(full)
    else:
        print("  Skipping gov.ie date fix (--skip-date-fix)")

    # 2. Filter for primary & secondary education
    full = filter_primary_secondary(full)

    # 3. Flag non-English language articles
    full = flag_language(full)

    # 4. Drop duplicate URLs
    before = len(full)
    full = full.drop_duplicates(subset=["url"])
    dupes = before - len(full)
    if dupes:
        print(f"  Dropped {dupes} duplicate rows")

    # Ensure all columns present
    for col in FINAL_COLS:
        if col not in full.columns:
            full[col] = ""

    out = Path(args.output) if args.output else INFERENCE_DIR / "ireland_inference.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    full[FINAL_COLS].to_csv(out, index=False)

    print(f"\n  Wrote {len(full)} rows to {out}")
    print(full["source"].value_counts().to_string())
    print(f"\n  By language:")
    print(full["language"].value_counts().to_string())


if __name__ == "__main__":
    main()
