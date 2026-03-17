import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import time
from datetime import datetime

# ----------------------------------------------------------
# Config
# ----------------------------------------------------------
BASE = "https://www.irishtimes.com"
START_URL = "https://www.irishtimes.com/ireland/education/"

_DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "data" / "test" / "ireland_irish_times_full.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# ----------------------------------------------------------
# Extract article links from listing page
# ----------------------------------------------------------
def extract_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if "/ireland/education/20" in href and href not in links:
            if not href.startswith("http"):
                href = BASE + href
            links.append(href)
    return list(dict.fromkeys(links))


# ----------------------------------------------------------
# Scrape a single article
# ----------------------------------------------------------
def scrape_article(url, since_date=None, until_date=None):
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
    except requests.RequestException as e:
        print(f"  Failed to fetch {url}: {e}")
        return None

    if r.status_code != 200:
        print(f"  HTTP {r.status_code} for {url}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # Date parsing
    pub_date = None
    date_tag = soup.find("time") or soup.find("meta", {"property": "article:published_time"})
    if date_tag:
        date_text = date_tag.get("datetime", "") or date_tag.get("content", "") or date_tag.get_text(strip=True)
        for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d %B %Y", "%B %d, %Y"]:
            try:
                pub_date = datetime.strptime(date_text[:19] if "T" in date_text else date_text, fmt).date()
                break
            except ValueError:
                continue

    if pub_date:
        if since_date and pub_date < since_date:
            return "STOP"
        if until_date and pub_date > until_date:
            return "SKIP"

    # Paywall detection
    paywall = soup.find(class_=lambda c: c and "paywall" in c.lower() if c else False)
    if paywall:
        print(f"    Paywalled — skipping: {url}")
        return None

    # Also check for subscriber-only markers
    sub_marker = soup.find(string=lambda s: s and "subscriber" in s.lower() and "only" in s.lower() if s else False)
    if sub_marker:
        print(f"    Subscriber-only — skipping: {url}")
        return None

    # Main content
    content = soup.find("article") or soup.find("div", class_=lambda c: c and "article" in c.lower() if c else False)
    if content:
        for t in content.find_all(["script", "style", "figure", "aside", "nav", "footer"]):
            t.decompose()
        text = "\n".join(
            p.get_text(" ", strip=True)
            for p in content.find_all("p")
            if p.get_text(strip=True)
        )
    else:
        text = ""

    return {
        "url": url,
        "title": title,
        "date": pub_date.strftime("%Y-%m-%d") if pub_date else "",
        "text": text,
    }


# ----------------------------------------------------------
# Main scraper
# ----------------------------------------------------------
def scrape_irish_times(since_date=None, until_date=None, output_path=None, append=False):
    all_articles = []
    seen = set()
    page = 1
    max_pages = 200  # safety limit

    print("Starting Irish Times Education scrape...")

    while page <= max_pages:
        if page == 1:
            url = START_URL
        else:
            url = f"{START_URL}{page}/"

        print(f"  Scraping page {page}: {url}")
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
        except requests.RequestException as e:
            print(f"  Failed to fetch listing page: {e}")
            break

        if r.status_code != 200:
            print(f"  HTTP {r.status_code} — stopping.")
            break

        links = extract_links(r.text)
        print(f"  Extracted {len(links)} article links")

        if not links:
            print("  No links found — stopping.")
            break

        stop = False
        for link in links:
            if link in seen:
                continue
            seen.add(link)

            result = scrape_article(link, since_date=since_date, until_date=until_date)

            if result == "STOP":
                print("  Reached cutoff date — stopping.")
                stop = True
                break
            if result == "SKIP":
                continue
            if result:
                all_articles.append(result)

            time.sleep(1)

        if stop:
            break

        print(f"  {len(all_articles)} articles collected so far")
        page += 1
        time.sleep(1)

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
    scrape_irish_times(output_path=_DEFAULT_OUTPUT)
