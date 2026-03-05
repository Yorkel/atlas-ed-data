import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import time
from datetime import datetime
import xml.etree.ElementTree as ET

# ----------------------------------------------------------
# Config
# ----------------------------------------------------------
BASE = "https://www.gov.ie"
SITEMAP_URL = "https://www.gov.ie/sitemap-en.xml"

_DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "data" / "training" / "ireland" / "gov_ie.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Filter for Department of Education URLs
DEPT_KEYWORDS = ["/department-of-education/", "/departments/education/"]

EDUCATION_KEYWORDS = [
    "education", "school", "teacher", "curriculum", "pupil",
    "student", "learning", "qualification", "exam", "attainment",
    "literacy", "numeracy", "childcare", "early years",
]


# ----------------------------------------------------------
# Get news/press URLs from sitemap
# ----------------------------------------------------------
def get_education_urls_from_sitemap(since_date=None, until_date=None):
    print("  Fetching sitemap...")
    r = requests.get(SITEMAP_URL, headers=HEADERS, timeout=30)
    root = ET.fromstring(r.content)
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    urls = []
    for url_elem in root.findall(".//s:url", ns):
        loc = url_elem.find("s:loc", ns)
        if loc is None:
            continue
        href = loc.text
        # Filter for Department of Education press releases and news
        if any(kw in href.lower() for kw in DEPT_KEYWORDS):
            if "/press-release/" in href or "/news/" in href or "/publication/" in href:
                urls.append(href)

    # If the sitemap is an index, parse child sitemaps
    for sitemap_elem in root.findall(".//s:sitemap", ns):
        loc = sitemap_elem.find("s:loc", ns)
        if loc is None:
            continue
        child_url = loc.text
        print(f"  Parsing child sitemap: {child_url}")
        try:
            r2 = requests.get(child_url, headers=HEADERS, timeout=30)
            child_root = ET.fromstring(r2.content)
            for url_elem in child_root.findall(".//s:url", ns):
                loc2 = url_elem.find("s:loc", ns)
                if loc2 is None:
                    continue
                href = loc2.text
                if any(kw in href.lower() for kw in DEPT_KEYWORDS):
                    if "/press-release/" in href or "/news/" in href or "/publication/" in href:
                        urls.append(href)
            time.sleep(0.3)
        except Exception as e:
            print(f"  Failed to parse child sitemap {child_url}: {e}")

    print(f"  Found {len(urls)} Department of Education URLs")
    return list(dict.fromkeys(urls))


# ----------------------------------------------------------
# Scrape a single article
# ----------------------------------------------------------
def scrape_article(url, since_date=None, until_date=None):
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
    except requests.RequestException as e:
        print(f"  Failed to fetch {url}: {e}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # Date parsing — gov.ie uses various formats
    pub_date = None
    date_tag = soup.find("time") or soup.find("span", class_=lambda c: c and "date" in c.lower() if c else False)
    if date_tag:
        date_text = date_tag.get("datetime", "") or date_tag.get_text(strip=True)
        for fmt in ["%Y-%m-%d", "%d %B %Y", "%d/%m/%Y", "%d %b %Y"]:
            try:
                pub_date = datetime.strptime(date_text[:10] if fmt == "%Y-%m-%d" else date_text, fmt).date()
                break
            except ValueError:
                continue

    if pub_date:
        if since_date and pub_date < since_date:
            return None
        if until_date and pub_date > until_date:
            return None

    # Main content
    content = soup.find("article") or soup.find("div", class_=lambda c: c and "content" in c.lower() if c else False)
    if content:
        for t in content.find_all(["script", "style", "figure", "aside", "nav"]):
            t.decompose()
        text = "\n".join(
            p.get_text(" ", strip=True)
            for p in content.find_all("p")
            if p.get_text(strip=True)
        )
    else:
        text = ""

    # Post-filter for education relevance
    combined = (title + " " + text).lower()
    if not any(kw in combined for kw in EDUCATION_KEYWORDS):
        return None

    return {
        "url": url,
        "title": title,
        "date": pub_date.strftime("%Y-%m-%d") if pub_date else "",
        "text": text,
    }


# ----------------------------------------------------------
# Main scraper
# ----------------------------------------------------------
def scrape_gov_ie(since_date=None, until_date=None, output_path=None, append=False):
    all_articles = []

    print("Starting Irish Government (Dept of Education) scrape (sitemap)...")

    urls = get_education_urls_from_sitemap(since_date=since_date, until_date=until_date)

    for i, url in enumerate(urls, 1):
        print(f"  [{i}/{len(urls)}] Scraping: {url}")

        result = scrape_article(url, since_date=since_date, until_date=until_date)
        if result:
            all_articles.append(result)

        if i % 50 == 0:
            print(f"  {len(all_articles)} education articles collected so far")

        time.sleep(0.5)

    print(f"  Done. {len(all_articles)} education articles from {len(urls)} total URLs")
    _save(all_articles, output_path, append)
    return all_articles


def _save(articles, output_path, append):
    if output_path is None:
        return
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(articles)
    mode = "a" if append else "w"
    header = not (append and out.exists())
    df.to_csv(out, mode=mode, header=header, index=False)
    print(f"  Saved {len(df)} articles -> {out}")


if __name__ == "__main__":
    scrape_gov_ie(output_path=_DEFAULT_OUTPUT)
