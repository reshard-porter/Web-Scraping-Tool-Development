"""Single-source adapter; no browser or login required."""
import re
import time
from decimal import Decimal
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup

BASE = "https://books.toscrape.com/"
SOURCE = "books-to-scrape"

class ScrapeError(Exception):
    pass

def safe_url(base, link):
    url = urljoin(base, link)
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "books.toscrape.com":
        raise ScrapeError("Unexpected external URL: " + url)
    return url

def parse_listing(html, url):
    soup = BeautifulSoup(html, "html.parser")
    links = [safe_url(url, a["href"]) for a in soup.select("article.product_pod h3 a[href]")]
    if not links:
        raise ScrapeError("No product links found; page layout may have changed")
    nxt = soup.select_one("li.next a[href]")
    return links, safe_url(url, nxt["href"]) if nxt else None

def parse_product(html, url):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.select_one(".product_main h1")
    price = soup.select_one(".product_main .price_color")
    image = soup.select_one(".item.active img")
    fields = {r.th.get_text(strip=True): r.td.get_text(" ", strip=True)
              for r in soup.select("table tr") if r.th and r.td}
    if not title or not price or not image or not fields.get("UPC"):
        raise ScrapeError("Missing required product fields: " + url)
    match = re.fullmatch(r"£([0-9]+\.[0-9]{2})", price.get_text(strip=True))
    if not match:
        raise ScrapeError("Unrecognized price: " + url)
    heading = soup.select_one("#product_description")
    description = heading.find_next_sibling("p") if heading else None
    return dict(source=SOURCE, source_id=fields["UPC"], title=title.get_text(" ", strip=True),
                price=Decimal(match.group(1)), currency="GBP",
                description=description.get_text(" ", strip=True) if description else "",
                image_url=safe_url(url, image["src"]), listing_url=url,
                availability=fields.get("Availability", ""))

class BooksClient:
    def __init__(self, delay=1):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "LearningCatalogScraper/1.0"
        self.last_request = 0

    def close(self):
        self.session.close()

    def get(self, url):
        safe_url(BASE, url)
        for attempt in range(3):
            time.sleep(max(0, self.delay - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            try:
                response = self.session.get(url, timeout=(10, 30), allow_redirects=False)
                if response.status_code in (403, 429):
                    raise ScrapeError(f"Source blocked or throttled ({response.status_code}); retry later")
                if 300 <= response.status_code < 400:
                    raise ScrapeError("Unexpected redirect; source needs review")
                if response.status_code >= 500:
                    if attempt == 2:
                        response.raise_for_status()
                    time.sleep(2 ** attempt)
                    continue
                response.raise_for_status()
                response.encoding = "utf-8"
                return response.text
            except (requests.Timeout, requests.ConnectionError):
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
        raise ScrapeError("Request attempts exhausted")

    def products(self, pages):
        url = BASE + "catalogue/page-1.html"
        seen = set()
        for _ in range(pages):
            links, next_url = parse_listing(self.get(url), url)
            for link in links:
                if link not in seen:
                    seen.add(link)
                    yield parse_product(self.get(link), link)
            if not next_url:
                break
            url = next_url
