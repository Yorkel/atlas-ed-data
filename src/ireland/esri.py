import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import time
from datetime import datetime

# ----------------------------------------------------------
# Config
# ----------------------------------------------------------
BASE = "https://www.esri.ie"
START_URL = "https://www.esri.ie/research-areas/education"

_DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "data" / "training" / "ireland" / "esri.csv"

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
    for article in soup.find_all("article"):
        a = article.find("a", href=True)
        if a:
            href = a["href"].strip()
            if not href.startswith("http"):
                href = BASE + href
            links.append(href)
    # Also check h3 headings with links
    for h3 in soup.find_all("h3"):
        a = h3.find("a", href=True)
        if a:
            href = a["href"].strip()
            if not href.startswith("http"):
                href = BASE + href
            if href not in links:
                links.append(href)
    return list(dict.fromkeys(links))


# ----------------------------------------------------------
# Extract next page URL
# ----------------------------------------------------------
def extract_next_page(html):
    soup = BeautifulSoup(html, "html.parser")
    next_a = soup.select_one("a.next, a[rel='next'], li.next a, a[title='Next']")
    if next_a and next_a.get("href"):
        href = next_a["href"].strip()
        return href if href.startswith("http") else BASE + href
    return None


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

    # Date parsing
    pub_date = None
    date_tag = soup.find("time") or soup.find("span", class_=lambda c: c and "date" in c.lower() if c else False)
    if date_tag:
        date_text = date_tag.get("datetime", "") or date_tag.get_text(strip=True)
        for fmt in ["%Y-%m-%d", "%d %B %Y", "%d/%m/%Y", "%B %d, %Y", "%d %b %Y"]:
            try:
                pub_date = datetime.strptime(date_text[:10] if fmt == "%Y-%m-%d" else date_text, fmt).date()
                break
            except ValueError:
                continue

    if pub_date:
        if since_date and pub_date < since_date:
            return "STOP"
        if until_date and pub_date > until_date:
            return "SKIP"

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

    return {
        "url": url,
        "title": title,
        "date": pub_date.strftime("%Y-%m-%d") if pub_date else "",
        "text": text,
    }


# ----------------------------------------------------------
# Main scraper
# ----------------------------------------------------------
def scrape_esri(since_date=None, until_date=None, output_path=None, append=False):
    all_articles = []
    seen = set()
    url = START_URL
    page = 1

    print("Starting ESRI scrape...")

    while url:
        print(f"  Scraping page {page}: {url}")
        r = requests.get(url, headers=HEADERS, timeout=30)
        links = extract_links(r.text)
        print(f"  Extracted {len(links)} article links")

        if not links:
            print("  No links found — stopping.")
            break

        for link in links:
            if link in seen:
                continue
            seen.add(link)
            print(f"    Scraping: {link}")

            result = scrape_article(link, since_date=since_date, until_date=until_date)

            if result == "STOP":
                print("  Reached cutoff date — stopping.")
                _save(all_articles, output_path, append)
                return all_articles
            if result == "SKIP":
                continue
            if result:
                all_articles.append(result)

            time.sleep(1)

        url = extract_next_page(r.text)
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
    scrape_esri(output_path=_DEFAULT_OUTPUT)
