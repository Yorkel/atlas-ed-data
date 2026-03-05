"""
Quick test: can we scrape a given URL?

Usage:
    python src/test_scrape.py "https://example.com/news"

Checks:
    1. Does the site respond (status code)?
    2. Does it block scrapers (403/429)?
    3. Can we parse HTML and find article-like content?
    4. Does it have an API (WordPress REST API check)?
"""

import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def test_url(url):
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    print(f"\n{'='*60}")
    print(f"Testing: {url}")
    print(f"{'='*60}")

    # 1. Basic request
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        print(f"\n[1] Status code: {r.status_code}")
        if r.status_code == 403:
            print("    BLOCKED — site returns 403 Forbidden")
        elif r.status_code == 429:
            print("    RATE LIMITED — site returns 429")
        elif r.status_code >= 400:
            print(f"    ERROR — {r.status_code}")
        else:
            print("    OK — site responds")
    except requests.RequestException as e:
        print(f"\n[1] FAILED to connect: {e}")
        return

    # 2. Parse HTML
    soup = BeautifulSoup(r.text, "html.parser")

    # Count article-like elements
    articles = soup.find_all("article")
    headings = soup.find_all(["h1", "h2", "h3"])
    links = soup.find_all("a", href=True)
    paragraphs = soup.find_all("p")

    print(f"\n[2] HTML content found:")
    print(f"    <article> tags: {len(articles)}")
    print(f"    Headings (h1-h3): {len(headings)}")
    print(f"    Links: {len(links)}")
    print(f"    Paragraphs: {len(paragraphs)}")

    # 3. Show first few headings
    if headings:
        print(f"\n[3] First 5 headings:")
        for h in headings[:5]:
            text = h.get_text(strip=True)[:80]
            print(f"    <{h.name}> {text}")

    # 4. Check for WordPress REST API
    print(f"\n[4] WordPress API check:")
    try:
        wp = requests.get(f"{base}/wp-json/wp/v2/posts?per_page=1",
                         headers=HEADERS, timeout=10)
        if wp.status_code == 200:
            posts = wp.json()
            if posts:
                print(f"    WordPress API available — found posts")
                print(f"    Sample title: {posts[0].get('title', {}).get('rendered', 'N/A')[:60]}")
            else:
                print("    API responds but returned no posts")
        else:
            print(f"    No WordPress API (status {wp.status_code})")
    except Exception:
        print("    No WordPress API found")

    # 5. Check robots.txt
    print(f"\n[5] robots.txt:")
    try:
        robots = requests.get(f"{base}/robots.txt", headers=HEADERS, timeout=10)
        if robots.status_code == 200:
            lines = robots.text.strip().split("\n")[:10]
            for line in lines:
                print(f"    {line}")
            if len(robots.text.strip().split("\n")) > 10:
                print(f"    ... ({len(robots.text.strip().split(chr(10)))} lines total)")
        else:
            print(f"    Not found (status {robots.status_code})")
    except Exception:
        print("    Could not fetch")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/test_scrape.py URL [URL2] [URL3] ...")
        sys.exit(1)

    for url in sys.argv[1:]:
        test_url(url)
