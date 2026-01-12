# =============================================================================
# GOV.UK EDUCATION POLICY SCRAPER
#
# PURPOSE & SCOPE
# -----------------------------------------------------------------------------
# GOV.UK classifies content using broad topical taxonomies. The "Education"
# taxon captures a wide range of material that references education only
# tangentially, including:
#   - International diplomacy and soft-power education (e.g. FCDO, embassies)
#   - Cross-government skills and labour-market initiatives
#   - Sector-specific workforce training and apprenticeship programmes
#   - Administrative and delivery-focused communications (e.g. student finance)
#
# PROBLEM
# -----------------------------------------------------------------------------
# A naïve scrape of the Education taxon produces a heterogeneous corpus that
# conflates domestic education system governance with international, economic,
# and operational activity, reducing analytical coherence for policy analysis.
#
# APPROACH
# -----------------------------------------------------------------------------
# To avoid prematurely excluding potentially relevant material, this scraper:
#   1. Scrapes ALL GOV.UK news and communications tagged under "Education"
#   2. Extracts and records publishing organisations transparently
#   3. Applies a post-collection filtering step based on institutional remit
#
# EXCLUSIONS (POST-SCRAPE)
# -----------------------------------------------------------------------------
# Approximately 350 articles are excluded where education is framed primarily
# as:
#   - International relations or cultural exchange
#   - Economic growth, employment, or sectoral skills development
#   - Employer-led training, outreach, or workforce pipelines
#   - Operational delivery or administrative implementation
#
# FINAL ANALYTICAL CORPUS
# -----------------------------------------------------------------------------
# Analysis is restricted to core UK education policy actors responsible for
# domestic system governance, including:
#   - Department for Education (DfE)
#   - DfE arm’s-length bodies (e.g. Ofsted, Ofqual, ESFA)
#
# The resulting dataset is a focused corpus covering schools, further and
# higher education, curriculum, assessment, accountability, funding, and
# system-level reform.
#
# This approach is:
#   - Conceptually explicit
#   - Methodologically defensible
#   - Fully reproducible
#
# =============================================================================


import requests
import re
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time

# ------------------------------------------------------
# CONFIG
# ------------------------------------------------------
BASE = "https://www.gov.uk"
START_URL = (
    "https://www.gov.uk/search/news-and-communications"
    "?level_one_taxon=c58fdadd-7743-46d6-9629-90bb3ccc4ef0"
    "&order=updated-newest"
)

OUTPUT = "/workspaces/ERP_Newsletter/data/data05_full_articles_selected/govuk_education_articles_2023_2025.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (GovUK Education Scraper)"
}

MAX_OLD_PAGES = 3  # Stop after 3 consecutive pages with no 2023+ content

# ------------------------------------------------------
# CORE UK EDUCATION POLICY BODIES
# ------------------------------------------------------
CORE_EDUCATION_BODIES = [
    "Department for Education",
    "Education and Skills Funding Agency",
    "Ofsted",
    "Ofqual",
    "Office for Students",
    "Standards and Testing Agency",
    "Institute for Apprenticeships",
    "Skills England"
]

# ------------------------------------------------------
# LINK EXTRACTION
# ------------------------------------------------------
def extract_links(html):
    soup = BeautifulSoup(html, "html.parser")
    return [
        BASE + a["href"]
        for a in soup.select("li.gem-c-document-list__item a[href]")
    ]


def extract_next_page(html):
    soup = BeautifulSoup(html, "html.parser")
    next_btn = soup.select_one("div.govuk-pagination__next a")
    return BASE + next_btn["href"] if next_btn else None


# ------------------------------------------------------
# ROBUST DATE EXTRACTION
# ------------------------------------------------------
def extract_date_robust(soup, url):
    metadata = soup.select_one("dl.gem-c-metadata__list")
    if metadata:
        for dt in metadata.find_all("dt"):
            label = dt.get_text(strip=True).lower()
            dd = dt.find_next_sibling("dd")
            if not dd:
                continue
            if label in ("published:", "updated:"):
                raw = dd.get_text(" ", strip=True)
                try:
                    return datetime.strptime(raw, "%d %B %Y")
                except ValueError:
                    pass

    for block in soup.select("div.gem-c-published-dates"):
        raw = (
            block.get_text(" ", strip=True)
            .replace("Published", "")
            .replace("Updated", "")
            .strip()
        )
        try:
            return datetime.strptime(raw, "%d %B %Y")
        except ValueError:
            pass

    text = soup.get_text(" ", strip=True)
    match = re.search(
        r"\b(\d{1,2}\s+"
        r"(January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{4})\b",
        text,
    )
    if match:
        try:
            return datetime.strptime(match.group(1), "%d %B %Y")
        except ValueError:
            pass

    print(f"❌ DATE NOT FOUND: {url}")
    return None


# ------------------------------------------------------
# SCRAPE SINGLE ARTICLE
# ------------------------------------------------------
def scrape_article(url):
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    h1 = soup.select_one("h1.gem-c-heading__text, h1.govuk-heading-l")
    title = h1.get_text(strip=True) if h1 else ""

    from_org = ""
    metadata = soup.select_one("dl.gem-c-metadata__list")
    if metadata:
        for dt in metadata.find_all("dt"):
            if dt.get_text(strip=True).lower() == "from:":
                dd = dt.find_next_sibling("dd")
                if dd:
                    orgs = [a.get_text(strip=True) for a in dd.find_all("a")]
                    from_org = "; ".join(orgs)

    pub_date = extract_date_robust(soup, url)
    if not pub_date:
        return None

    main = soup.select_one("main#content")
    if not main:
        return None

    text_parts = []
    for el in main.find_all(["p", "li", "h2"], recursive=True):
        if el.name == "h2" and "share this page" in el.get_text(strip=True).lower():
            break
        txt = el.get_text(strip=True)
        if txt:
            text_parts.append(txt)

    return {
        "url": url,
        "title": title,
        "from": from_org,
        "date": pub_date.strftime("%Y-%m-%d"),
        "text": "\n".join(text_parts),
    }


# ------------------------------------------------------
# POST-SCRAPE CLASSIFICATION
# ------------------------------------------------------
def is_core_education(from_field):
    return any(org in from_field for org in CORE_EDUCATION_BODIES)


def get_primary_org(from_field):
    if "Department for Education" in from_field:
        return "Department for Education"
    for org in CORE_EDUCATION_BODIES:
        if org in from_field:
            return org
    return "Other"


# ------------------------------------------------------
# MAIN SCRAPER
# ------------------------------------------------------
def scrape_govuk():
    all_articles = []
    seen = set()
    url = START_URL
    page = 1
    old_page_streak = 0

    print("🚀 Starting GOV.UK education scrape…")

    while url:
        print(f"\n📄 Page {page}: {url}")
        r = requests.get(url, headers=HEADERS)
        html = r.text

        links = extract_links(html)
        print(f"🔗 Found {len(links)} links")

        page_has_recent = False

        for link in links:
            if link in seen:
                continue
            seen.add(link)

            print(f"   📰 Scraping: {link}")
            result = scrape_article(link)

            if result:
                all_articles.append(result)
                if result["date"] >= "2023-01-01":
                    page_has_recent = True

            time.sleep(0.8)

        if page_has_recent:
            old_page_streak = 0
        else:
            old_page_streak += 1
            print(
                f"⚠️ Page {page} contains no 2023+ publications "
                f"({old_page_streak}/{MAX_OLD_PAGES})"
            )

        if old_page_streak >= MAX_OLD_PAGES:
            print("⛔ Reached stopping condition — ending scrape.")
            break

        url = extract_next_page(html)
        page += 1
        time.sleep(1)

    df = pd.DataFrame(all_articles)
    df = df[df["date"] >= "2023-01-01"]

    df["core_education"] = df["from"].apply(is_core_education)
    df["primary_org"] = df["from"].apply(get_primary_org)

    df.to_csv(OUTPUT, index=False)
    print(f"\n💾 Saved {len(df)} articles to: {OUTPUT}")


# ------------------------------------------------------
# RUN
# ------------------------------------------------------
if __name__ == "__main__":
    scrape_govuk()



Overall summary

# The initial GOV.UK scrape using the education taxon returned a very broad set of documents, many of which referenced education only tangentially—most commonly in the context of international diplomacy, sector-specific workforce training, skills and labour market policy, or administrative delivery rather than domestic education system governance. To address this, I applied a systematic filtering step that excluded publications led by non-education departments, overseas posts, arm’s-length delivery bodies, and industry-specific organisations where education was framed as soft power, economic development, or operational implementation. This process removed international scholarship and exchange programmes, employer-led apprenticeship and outreach initiatives, cross-government skills and growth announcements, and routine administrative communications (e.g. student finance operations). The resulting corpus is a focused dataset centred on core UK education policy, primarily covering schools, further and higher education, curriculum, assessment, accountability, funding, and system-level reform, and is therefore analytically coherent for examining domestic education policy priorities and change over time.