from __future__ import annotations

from ..config import Settings
from ..models import SearchPage, SearchResult
from ..utils.http import HttpClient, ProviderUnavailable
from .base import SearchProvider


class SerpApiShoppingProvider(SearchProvider):
    mode = "shopping"

    def __init__(self, settings: Settings, http: HttpClient) -> None:
        self.key = settings.serpapi_api_key
        self.http = http

    async def search(self, query: str, page: int = 1) -> SearchPage:
        if not self.key:
            raise ProviderUnavailable("SERPAPI_API_KEY is not configured.")
        response = await self.http.request(
            "GET",
            "https://serpapi.com/search.json",
            params={
                "engine": "google_shopping",
                "q": query,
                "start": (page - 1) * 10,
                "num": 10,
                "api_key": self.key,
            },
        )
        results = []
        for item in response.get("shopping_results", []):
            # Only display a price when the provider supplied one.
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link") or item.get("product_link", ""),
                    source=item.get("source", ""),
                    price=item.get("price", ""),
                    store=item.get("source", ""),
                    description=item.get("snippet", ""),
                    image_url=item.get("thumbnail"),
                )
            )
        total = len(results)
        return SearchPage(query, self.mode, page, max(1, min(10, (total + 9) // 10)), [r for r in results if r.url])
