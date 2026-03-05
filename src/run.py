# Education Policy Scraper — pipeline entry point.
#
# MODE A — full retrospective (no --since flag):
#   python run.py --country eng
#   Scrapes all England sources back to 2023-01-01.
#   Output: per-source CSVs in data/training/england/
#           then run england/merge.py to produce data/training/training_data.csv
#
# MODE B — training top-up (--since and --until <= TRAINING_CUTOFF):
#   python run.py --country eng --since 2025-12-05 --until 2025-12-31
#   Appends new articles to existing training CSVs. Run england/merge.py afterwards.
#
# MODE C — weekly inference (--since and --until after TRAINING_CUTOFF):
#   python run.py --country eng --since 2026-02-21 --until 2026-02-27 --week 9
#   Writes one merged CSV to data/inference/england/week09_2026-02-27.csv
#
# Scotland / Ireland — retrospective (one-time, Jan 2023 → 20 Feb 2026):
#   python run.py --country sco --until 2026-02-20
#   python run.py --country irl --until 2026-02-20
#   → data/inference/scotland/2026-02-20.csv
#   → data/inference/ireland/2026-02-20.csv
#   Scotland and Ireland are inference-only (Phase 1). All data goes to data/inference/.
#
# Weekly inference (all three countries, from 21 Feb 2026 onwards):
#   python run.py --country eng --since 2026-02-21 --until 2026-02-27 --week 9
#   python run.py --country sco --since 2026-02-21 --until 2026-02-27 --week 9
#   python run.py --country irl --since 2026-02-21 --until 2026-02-27 --week 9
#
# GitHub Actions calls Mode C automatically each Monday for all three countries.

import argparse
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from england.dfe import scrape_govuk
from england.epi import scrape_epi
from england.nuffield import scrape_nuffield
from england.fftlabs import scrape_fft_datalab
from england.fed import scrape_fed

from scotland.gov_scot import scrape_gov_scot
from scotland.education_scotland import scrape_education_scotland
from scotland.sera import scrape_sera
from scotland.audit_scotland import scrape_audit_scotland
from scotland.gtcs import scrape_gtcs
from scotland.tes_scotland import scrape_tes_scotland

from ireland.gov_ie import scrape_gov_ie
from ireland.esri import scrape_esri
from ireland.tasc import scrape_tasc
from ireland.erc import scrape_erc
from ireland.teaching_council import scrape_teaching_council
from ireland.education_matters import scrape_education_matters

try:
    from england.schoolsweek import scrape_schoolsweek
    _HAS_SCHOOLSWEEK = True
except ImportError:
    _HAS_SCHOOLSWEEK = False

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data"

TRAINING_CUTOFF = date(2025, 12, 31)  # articles up to this date = training data

# Default retrospective start per country
RETROSPECTIVE_START = {
    "eng": date(2023, 1, 1),
    "sco": date(2023, 1, 1),
    "irl": date(2023, 1, 1),
}

COUNTRY_DIR = {
    "eng": "england",
    "sco": "scotland",
    "irl": "ireland",
}

# Countries whose data goes to training (England only until Phase 2)
TRAINING_COUNTRIES = {"eng"}

# Per-source training CSV filenames (country subfolder added at runtime)
TRAINING_FILENAMES = {
    "schoolsweek": "schoolsweek.csv",
    "gov":         "govuk_education.csv",
    "epi":         "epi.csv",
    "nuffield":    "nuffield.csv",
    "fft":         "fft_education_datalab.csv",
    "fed":         "fed.csv",
}

# Scrapers grouped by country code — add Scotland/Ireland entries here when ready
SCRAPERS = {
    "eng": [],   # populated below after optional import
    "sco": [
        ("gov_scot",            scrape_gov_scot),
        ("education_scotland",  scrape_education_scotland),
        ("sera",                scrape_sera),
        ("audit_scotland",      scrape_audit_scotland),
        ("gtcs",                scrape_gtcs),
        ("tes_scotland",        scrape_tes_scotland),
    ],
    "irl": [
        ("gov_ie",              scrape_gov_ie),
        ("esri",                scrape_esri),
        ("tasc",                scrape_tasc),
        ("erc",                 scrape_erc),
        ("teaching_council",    scrape_teaching_council),
        ("education_matters",   scrape_education_matters),
    ],
}

_eng = SCRAPERS["eng"]
if _HAS_SCHOOLSWEEK:
    _eng.append(("schoolsweek", scrape_schoolsweek))
_eng += [
    ("gov",      scrape_govuk),
    ("epi",      scrape_epi),
    ("nuffield", scrape_nuffield),
    ("fft",      scrape_fft_datalab),
    ("fed",      scrape_fed),
]

# Metadata added to merged output — extend when Scotland/Ireland sources are added
SOURCE_META = {
    "schoolsweek": {"country": "eng", "type": "ed_journalism", "institution_name": "Schools Week"},
    "gov":         {"country": "eng", "type": "government",    "institution_name": None},  # uses primary_org
    "epi":         {"country": "eng", "type": "think_tank",    "institution_name": "Education Policy Institute"},
    "nuffield":    {"country": "eng", "type": "think_tank",    "institution_name": "Nuffield Foundation"},
    "fft":         {"country": "eng", "type": "ed_res_org",    "institution_name": "FFT Education Datalab"},
    "fed":         {"country": "eng", "type": "prof_body",     "institution_name": "Foundation for Educational Development"},
    # Scotland
    "gov_scot":           {"country": "sco", "type": "government",    "institution_name": "Scottish Government"},
    "education_scotland": {"country": "sco", "type": "gov_agency",    "institution_name": "Education Scotland"},
    "sera":               {"country": "sco", "type": "think_tank",    "institution_name": "SERA"},
    "audit_scotland":     {"country": "sco", "type": "ed_res_org",    "institution_name": "Audit Scotland"},
    "gtcs":               {"country": "sco", "type": "prof_body",     "institution_name": "GTCS"},
    "tes_scotland":       {"country": "sco", "type": "ed_journalism", "institution_name": "TES Scotland"},
    # Ireland
    "gov_ie":             {"country": "irl", "type": "government",    "institution_name": "Department of Education (Ireland)"},
    "esri":               {"country": "irl", "type": "think_tank",    "institution_name": "ESRI"},
    "tasc":               {"country": "irl", "type": "think_tank",    "institution_name": "TASC"},
    "erc":                {"country": "irl", "type": "ed_res_org",    "institution_name": "Educational Research Centre"},
    "teaching_council":   {"country": "irl", "type": "prof_body",     "institution_name": "Teaching Council"},
    "education_matters":  {"country": "irl", "type": "ed_journalism", "institution_name": "Education Matters"},
}

FINAL_COLS = ["url", "title", "date", "text", "source", "country", "type", "institution_name"]


def parse_args():
    parser = argparse.ArgumentParser(description="Education Policy Scraper")
    parser.add_argument(
        "--country",
        choices=["eng", "sco", "irl"],
        default="eng",
        help="Which country's sources to scrape (default: eng).",
    )
    parser.add_argument(
        "--since",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(),
        default=None,
        help="Only scrape articles published on or after this date (YYYY-MM-DD). "
             "Omit for full retrospective scrape from this country's default start.",
    )
    parser.add_argument(
        "--until",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(),
        default=None,
        help="Only scrape articles published on or before this date (YYYY-MM-DD). "
             f"Articles up to {TRAINING_CUTOFF} go to data/training/; "
             "later articles go to data/inference/.",
    )
    parser.add_argument(
        "--week",
        type=int,
        default=None,
        help="Week number to include in the inference output filename (e.g. --week 1 → week01_YYYY-MM-DD.csv). "
             "Only used for inference runs.",
    )
    return parser.parse_args()


def _enrich(rows, name):
    """Add source / country / type / institution_name columns to a list of row dicts."""
    if not rows:
        return None
    df = pd.DataFrame(rows)
    meta = SOURCE_META[name]
    df["source"] = name
    df["country"] = meta["country"]
    df["type"] = meta["type"]
    if name == "gov":
        if "core_education" in df.columns:
            df = df[df["core_education"] == True].copy()
        df["institution_name"] = df["primary_org"] if "primary_org" in df.columns else "Government"
    else:
        df["institution_name"] = meta["institution_name"]
    return df[[c for c in FINAL_COLS if c in df.columns]]


def _write_scrape_log(inference_dir, since_date, until_date, filename, frames, country):
    from datetime import datetime
    log_path = ROOT / "docs" / "scrape_log.md"
    run_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    since_str = since_date.strftime("%Y-%m-%d")
    until_str = until_date.strftime("%Y-%m-%d") if until_date else "present"
    total = sum(len(f) for f in frames)

    counts = {f["source"].iloc[0]: len(f) for f in frames if "source" in f.columns}
    source_summary = ", ".join(f"{s}={n}" for s, n in counts.items())

    row = f"| {run_time} | {country} | {since_str} → {until_str} | {filename} | {source_summary} | **{total}** |\n"

    if not log_path.exists():
        header = (
            "# Inference Scrape Log\n\n"
            "| Run time | Country | Date range | File | Sources | Total |\n"
            "|----------|---------|------------|------|---------|-------|\n"
        )
        log_path.write_text(header + row)
    else:
        with open(log_path, "a") as f:
            f.write(row)

    print(f"📋 Scrape log updated → {log_path}")


def _validate_inference(df, filename):
    """Basic sanity checks on a merged inference CSV. Prints warnings but does not exit."""
    issues = []

    missing_cols = [c for c in FINAL_COLS if c not in df.columns]
    if missing_cols:
        issues.append(f"missing columns: {missing_cols}")

    empty_text = df["text"].isna().sum() + (df["text"].str.strip() == "").sum()
    if empty_text:
        issues.append(f"{empty_text} rows have empty text")

    if len(df) == 0:
        issues.append("no articles — check scrapers")
    elif len(df) < 5:
        issues.append(f"only {len(df)} articles — unusually low, verify sources")

    if issues:
        print(f"\n⚠️  Validation warnings for {filename}:")
        for issue in issues:
            print(f"   • {issue}")
    else:
        print(f"✅ Validation passed: {len(df)} articles, all columns present, no empty text")


def main():
    args = parse_args()
    country = args.country
    country_dir = COUNTRY_DIR[country]
    since_date = args.since or RETROSPECTIVE_START[country]
    until_date = args.until

    if args.since is None:
        print(f"MODE A — retrospective scrape [{country}] from {since_date}")
    else:
        print(f"MODE B/C — incremental scrape [{country}] {since_date} → {until_date or 'present'}")

    # Scotland and Ireland always go to inference (Phase 1)
    # England goes to training if until_date <= TRAINING_CUTOFF, otherwise inference
    if country not in TRAINING_COUNTRIES:
        is_training = False
    else:
        is_training = until_date is None or until_date <= TRAINING_CUTOFF

    training_dir = DATA_ROOT / "training" / country_dir
    inference_dir = DATA_ROOT / "inference" / country_dir
    output_dir = training_dir if is_training else inference_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    append = is_training and args.since is not None

    mode_label = (
        "training (append)"    if append else
        "training (overwrite)" if is_training else
        "inference → one merged file"
    )
    print(f"Output  → {output_dir}  [{mode_label}]")

    scrapers = SCRAPERS.get(country, [])
    if not scrapers:
        print(f"⚠️  No scrapers registered for --country {country} yet.")
        return

    total = 0
    inference_frames = []

    for name, scrape_fn in scrapers:
        print(f"\n{'='*50}")
        print(f"Scraping: {name}")
        print(f"{'='*50}")
        try:
            if is_training:
                output_path = training_dir / TRAINING_FILENAMES[name]
                output_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                output_path = None  # scrapers return rows; we merge below

            rows = scrape_fn(
                since_date=since_date,
                until_date=until_date,
                output_path=output_path,
                append=append,
            )
            count = len(rows) if rows else 0
            total += count
            print(f"✅ {name}: {count} articles")

            if not is_training and rows:
                df = _enrich(rows, name)
                if df is not None:
                    inference_frames.append(df)

        except Exception as e:
            print(f"❌ {name} failed: {e}")

    # Write single merged inference CSV — named by week number + Friday (until_date)
    if not is_training and inference_frames:
        until_str = until_date.strftime("%Y-%m-%d") if until_date else "present"
        if args.week is not None:
            filename_stem = f"week{args.week:02d}_{until_str}"
        else:
            filename_stem = until_str
        out = inference_dir / f"{filename_stem}.csv"
        merged = pd.concat(inference_frames, ignore_index=True)
        merged.to_csv(out, index=False)
        print(f"\n✅ Wrote {len(merged)} articles to {out}")
        _write_scrape_log(inference_dir, since_date, until_date, out.name, inference_frames, country)
        _validate_inference(merged, out.name)

    print(f"\n{'='*50}")
    print(f"Done. Total articles scraped: {total}")
    if is_training:
        print("Next step: run merge.py to update data/training/training_data.csv")


if __name__ == "__main__":
    main()
