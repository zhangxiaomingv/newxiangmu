"""Website crawler using httpx + BeautifulSoup."""

import json
import re
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

from app.config import CRAWL_TIMEOUT, USER_AGENT


async def crawl_brand(brand: str, url: str | None = None) -> dict:
    """
    Crawl brand information.

    - If URL provided, scrape that site
    - If brand name, search for site and scrape
    """
    target_url = url or await _discover_url(brand)
    page_data = None
    about_content = ""

    if target_url:
        page_data = await _scrape_page(target_url)
        # Also try to find and scrape About page
        about_url = _find_about_page(page_data["soup"], target_url)
        if about_url:
            about_data = await _scrape_page(about_url)
            about_content = about_data["raw_text"]

    return {
        "url": target_url or f"https://{brand.lower().replace(' ', '')}.com",
        "title": page_data["title"] if page_data else brand,
        "meta_description": page_data["meta_description"] if page_data else "",
        "raw_text": page_data["raw_text"] if page_data else f"[No crawl data available for {brand}]",
        "about_text": about_content,
        "structured_data": page_data["structured_data"] if page_data else {},
        "headings": page_data["headings"] if page_data else [],
    }


async def _discover_url(brand: str) -> str | None:
    """Try common URL patterns for a brand name."""
    # Clean brand name to likely domain
    slug = brand.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "", slug)
    if not slug:
        return None

    candidates = [
        f"https://{slug}.com",
        f"https://www.{slug}.com",
        f"https://{slug}.io",
        f"https://www.{slug}.io",
    ]

    async with httpx.AsyncClient(timeout=CRAWL_TIMEOUT / 1000) as client:
        for c in candidates:
            try:
                r = await client.head(c, follow_redirects=True, headers={"User-Agent": USER_AGENT})
                if r.status_code < 400:
                    return str(r.url)
            except Exception:
                continue
    return None


async def _scrape_page(url: str) -> dict:
    """Scrape a single page and extract content."""
    async with httpx.AsyncClient(timeout=CRAWL_TIMEOUT / 1000, follow_redirects=True) as client:
        try:
            r = await client.get(url, headers={"User-Agent": USER_AGENT})
            r.raise_for_status()
        except Exception as e:
            return {
                "title": "",
                "meta_description": "",
                "raw_text": f"[Error fetching {url}: {e}]",
                "structured_data": {},
                "headings": [],
                "soup": None,
            }

    soup = BeautifulSoup(r.text, "html.parser")

    # Remove script/style content
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"].strip()

    # Structured data (JSON-LD)
    structured_data = {}
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                structured_data.update(data)
            elif isinstance(data, list) and data:
                structured_data.update(data[0] if isinstance(data[0], dict) else {})
        except Exception:
            continue

    # Extract headings
    headings = []
    for h in soup.find_all(["h1", "h2", "h3"]):
        text = h.get_text(strip=True)
        if text:
            headings.append({"level": h.name, "text": text})

    # Clean text
    raw_text = soup.get_text(separator="\n", strip=True)
    raw_text = re.sub(r"\n{3,}", "\n\n", raw_text)
    raw_text = raw_text[:10000]  # Limit to ~10k chars

    return {
        "title": title,
        "meta_description": meta_desc,
        "raw_text": raw_text,
        "structured_data": structured_data,
        "headings": headings,
        "soup": soup,
    }


def _find_about_page(soup: BeautifulSoup | None, base_url: str) -> str | None:
    """Try to find an About page link."""
    if soup is None:
        return None
    about_keywords = ["about", "about-us", "about_us", "company", "who-we-are"]
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        for kw in about_keywords:
            if kw in href:
                return urljoin(base_url, a["href"])
    return None
