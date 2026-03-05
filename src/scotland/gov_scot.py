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
BASE = "https://www.gov.scot"
SITEMAP_INDEX = "https://www.gov.scot/sitemap.xml"

_DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "data" / "training" / "scotland" / "gov_scot.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Education-related keywords for filtering (post-scrape)
EDUCATION_KEYWORDS = [
    "education", "school", "teacher", "curriculum", "pupil",
    "student", "learning", "qualification", "exam", "attainment",
    "literacy", "numeracy", "childcare", "early years", "SQA",
]


# ----------------------------------------------------------
# Get news URLs from monthly sitemaps
# ----------------------------------------------------------
def get_news_urls_from_sitemaps(since_date=None, until_date=None):
    print("  Fetching sitemap index...")
    r = requests.get(SITEMAP_INDEX, headers=HEADERS, timeout=30)
    root = ET.fromstring(r.content)
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    monthly_sitemaps = []
    for sitemap in root.findall("s:sitemap", ns):
        loc = sitemap.find("s:loc", ns).text
        # Filter to relevant year/month sitemaps
        if "/sitemap/" in loc and loc != SITEMAP_INDEX:
            # Extract year/month from URL like sitemap/2025/1.xml
            parts = loc.rstrip(".xml").split("/")
            try:
                year = int(parts[-2])
                month = int(parts[-1])
                sitemap_date = datetime(year, month, 1).date()
                if since_date and sitemap_date.year < since_date.year:
                    continue
                if until_date and sitemap_date > until_date:
                    continue
                monthly_sitemaps.append(loc)
            except (ValueError, IndexError):
                if "latest" in loc:
                    monthly_sitemaps.append(loc)

    print(f"  Found {len(monthly_sitemaps)} relevant monthly sitemaps")

    news_urls = []
    for sitemap_url in monthly_sitemaps:
        print(f"  Parsing: {sitemap_url}")
        r = requests.get(sitemap_url, headers=HEADERS, timeout=30)
        root = ET.fromstring(r.content)
        for url_elem in root.findall("s:url", ns):
            loc = url_elem.find("s:loc", ns).text
            if "/news/" in loc:
                news_urls.append(loc)
        time.sleep(0.3)

    print(f"  Total news URLs found: {len(news_urls)}")
    return list(dict.fromkeys(news_urls))


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

    # Date — gov.scot uses <dl> with "Published" label
    pub_date = None
    for dt in soup.find_all("dt"):
        if "published" in dt.get_text(strip=True).lower():
            dd = dt.find_next_sibling("dd")
            if dd:
                date_text = dd.get_text(strip=True)
                for fmt in ["%d %B %Y", "%Y-%m-%d"]:
                    try:
                        pub_date = datetime.strptime(date_text, fmt).date()
                        break
                    except ValueError:
                        continue

    if pub_date:
        if since_date and pub_date < since_date:
            return None
        if until_date and pub_date > until_date:
            return None

    # Main content
    content = soup.find("div", class_="body-content") or soup.find("article")
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
def scrape_gov_scot(since_date=None, until_date=None, output_path=None, append=False):
    all_articles = []

    print("Starting Scottish Government scrape (sitemap)...")

    news_urls = get_news_urls_from_sitemaps(since_date=since_date, until_date=until_date)

    for i, url in enumerate(news_urls, 1):
        print(f"  [{i}/{len(news_urls)}] Scraping: {url}")

        result = scrape_article(url, since_date=since_date, until_date=until_date)
        if result:
            all_articles.append(result)

        if i % 50 == 0:
            print(f"  {len(all_articles)} education articles collected so far")

        time.sleep(0.5)

    print(f"  Done. {len(all_articles)} education articles from {len(news_urls)} total news items")
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
    scrape_gov_scot(output_path=_DEFAULT_OUTPUT)
