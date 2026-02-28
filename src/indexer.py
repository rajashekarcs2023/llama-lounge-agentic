"""Multi-site doc indexer using llms.txt.

Strategy:
1. Fetch {base_url}/llms.txt — a standardized file that doc sites publish
   for LLM consumption. Contains structured page listings with URLs.
2. Parse the page index from llms.txt (categorized URLs + titles).
3. Fetch individual pages via their .md endpoints — clean markdown, no HTML parsing.
4. Fallback to raw requests if llms.txt is not available.
"""

import re
from urllib.parse import urljoin

import requests

from src.cache import cache
from config.settings import MAX_PAGES_PER_SITE


def _parse_llms_txt(base_url: str, text: str) -> list[dict]:
    """Parse an llms.txt file into a list of page entries.
    
    llms.txt format typically contains:
    - Section headers (## Category)
    - Markdown links: - https://docs.example.com/page.md
    - Or bullet links: - [Title](url)
    """
    pages = []
    seen = set()
    current_section = "General"

    for line in text.split("\n"):
        line = line.strip()

        # Track section headers
        if line.startswith("## "):
            current_section = line[3:].strip()
            continue
        if line.startswith("# "):
            continue

        # Match bare URLs (common in llms.txt)
        if line.startswith("- http") or line.startswith("* http"):
            url = line.lstrip("-* ").strip()
            if url not in seen:
                seen.add(url)
                # Derive title from URL path
                path = url.split("/")[-1].replace(".md", "").replace("-", " ").replace("_", " ")
                title = path.title() if path else current_section
                pages.append({
                    "url": url,
                    "title": title,
                    "section": current_section,
                    "description": f"{current_section} > {title}",
                })

        # Match markdown links: [Title](url)
        matches = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', line)
        for title, url in matches:
            full_url = url if url.startswith("http") else urljoin(base_url, url)
            if full_url not in seen:
                seen.add(full_url)
                pages.append({
                    "url": full_url,
                    "title": title,
                    "section": current_section,
                    "description": f"{current_section} > {title}",
                })

    return pages


def _fetch_llms_txt(base_url: str) -> str | None:
    """Try to fetch llms.txt from a doc site."""
    for path in ["/llms.txt", "/llms-full.txt"]:
        url = base_url.rstrip("/") + path
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200 and len(resp.text) > 100:
                return resp.text
        except Exception:
            continue
    return None


def _fallback_index(base_url: str) -> list[dict]:
    """Fallback: scrape the index page for links if llms.txt is unavailable."""
    try:
        resp = requests.get(base_url, timeout=15)
        resp.raise_for_status()
        # Simple regex to find internal doc links
        urls = re.findall(r'href=["\']([^"\']+)["\']', resp.text)
        pages = []
        seen = set()
        for href in urls:
            full_url = href if href.startswith("http") else urljoin(base_url, href)
            if base_url in full_url and full_url not in seen:
                if any(full_url.endswith(ext) for ext in [".png", ".jpg", ".css", ".js", ".svg"]):
                    continue
                seen.add(full_url)
                path = full_url.split("/")[-1].replace("-", " ").replace("_", " ").replace(".html", "")
                pages.append({
                    "url": full_url,
                    "title": path.title() if path else "Home",
                    "section": "General",
                    "description": "",
                })
        return pages[:MAX_PAGES_PER_SITE]
    except Exception as e:
        print(f"   ✗ Fallback indexing failed for {base_url}: {e}")
        return []


def index_site(url: str, force: bool = False) -> list[dict]:
    """Index a documentation site and cache the results.
    
    Strategy: llms.txt first, fallback to HTML scraping.
    
    Args:
        url: Root URL of the doc site (e.g., 'https://docs.composio.dev')
        force: If True, re-index even if already cached
        
    Returns:
        List of page dicts with url, title, section, description
    """
    url = url.rstrip("/")

    if not force and cache.has_index(url):
        pages = cache.get_index(url)
        print(f"   Using cached index for {url} ({len(pages)} pages)")
        return pages

    print(f"   Indexing {url}...")

    # Try llms.txt first
    llms_text = _fetch_llms_txt(url)
    if llms_text:
        pages = _parse_llms_txt(url, llms_text)
        print(f"   ✓ Found {len(pages)} pages via llms.txt")
    else:
        print(f"   llms.txt not found, using fallback...")
        pages = _fallback_index(url)

    pages = pages[:MAX_PAGES_PER_SITE]

    if pages:
        cache.set_index(url, pages)
        print(f"   ✓ Indexed {len(pages)} pages from {url}")
    else:
        print(f"   ✗ No pages found for {url}")

    return pages


def fetch_pages(urls: list[str]) -> dict[str, str]:
    """Fetch specific doc pages and return their content as clean markdown.
    
    Strategy:
    - If URL ends with .md, fetch directly (clean markdown).
    - If URL doesn't end with .md, try appending .md first.
    - Fallback to fetching raw HTML and extracting text.
    
    Args:
        urls: List of page URLs to fetch
        
    Returns:
        Dict mapping URL to markdown content
    """
    results = {}

    for url in urls:
        if cache.has_page(url):
            results[url] = cache.get_page(url)
            continue

        content = None

        # Strategy 1: URL already ends in .md — fetch directly
        if url.endswith(".md"):
            try:
                resp = requests.get(url, timeout=15)
                if resp.status_code == 200:
                    content = resp.text
            except Exception:
                pass

        # Strategy 2: Try appending .md to get markdown version
        if content is None and not url.endswith(".md"):
            md_url = url.rstrip("/") + ".md"
            try:
                resp = requests.get(md_url, timeout=15)
                if resp.status_code == 200 and len(resp.text) > 50:
                    content = resp.text
            except Exception:
                pass

        # Strategy 3: Fetch raw page and extract text (no BS4, just regex)
        if content is None:
            try:
                resp = requests.get(url, timeout=15)
                if resp.status_code == 200:
                    # Strip HTML tags with regex (lightweight, no BS4)
                    text = re.sub(r'<script[^>]*>.*?</script>', '', resp.text, flags=re.DOTALL)
                    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
                    text = re.sub(r'<[^>]+>', '\n', text)
                    # Clean up whitespace
                    lines = [line.strip() for line in text.split("\n") if line.strip()]
                    content = "\n".join(lines)
            except Exception as e:
                content = f"[Error fetching {url}: {e}]"

        # Truncate very long pages
        if content and len(content) > 15000:
            content = content[:15000] + "\n... [truncated]"

        if content:
            cache.set_page(url, content)
            results[url] = content
        else:
            results[url] = f"[Error: could not fetch {url}]"

    return results
