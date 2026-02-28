"""In-memory cache for page indexes and fetched page content."""

from typing import Optional


class DocCache:
    """Simple in-memory cache for doc site indexes and fetched pages."""

    def __init__(self):
        self._indexes: dict[str, list[dict]] = {}
        self._pages: dict[str, str] = {}

    def set_index(self, site_url: str, pages: list[dict]) -> None:
        self._indexes[site_url] = pages

    def get_index(self, site_url: str) -> Optional[list[dict]]:
        return self._indexes.get(site_url)

    def has_index(self, site_url: str) -> bool:
        return site_url in self._indexes

    def get_all_indexes(self) -> dict[str, list[dict]]:
        return dict(self._indexes)

    def get_unified_index(self) -> list[dict]:
        """Return a flat list of all pages across all indexed sites."""
        unified = []
        for site_url, pages in self._indexes.items():
            for page in pages:
                unified.append({**page, "source": site_url})
        return unified

    def set_page(self, url: str, content: str) -> None:
        self._pages[url] = content

    def get_page(self, url: str) -> Optional[str]:
        return self._pages.get(url)

    def has_page(self, url: str) -> bool:
        return url in self._pages

    def stats(self) -> dict:
        return {
            "indexed_sites": len(self._indexes),
            "total_pages_indexed": sum(len(p) for p in self._indexes.values()),
            "pages_fetched": len(self._pages),
        }


# Global singleton
cache = DocCache()
