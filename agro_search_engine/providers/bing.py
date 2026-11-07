from __future__ import annotations

from email.utils import parsedate_to_datetime

from ..config import Settings
from ..models import SearchPage, SearchResult
from ..utils.http import HttpClient, ProviderUnavailable
from .base import SearchProvider


class BingProvider(SearchProvider):
    def __init__(self, settings: Settings, http: HttpClient, mode: str) -> None:
        self.key = settings.bing_search_api_key
        self.endpoint = settings.bing_search_endpoint
        self.http = http
        self.mode = mode

    async def search(self, query: str, page: int = 1) -> SearchPage:
        if not self.key:
            raise ProviderUnavailable("BING_SEARCH_API_KEY is not configured.")
        endpoint = {
            "images": "images/search",
            "news": "news/search",
            "videos": "videos/search",
        }[self.mode]
        response = await self.http.request(
            "GET",
            f"{self.endpoint}/{endpoint}",
            params={
                "q": query,
                "count": 8,
                "offset": (page - 1) * 8,
                "safeSearch": "Strict",
                "mkt": "en-US",
            },
            headers={"Ocp-Apim-Subscription-Key": self.key},
        )
        items = response.get(
            {"images": "value", "news": "value", "videos": "value"}[self.mode], []
        )
        results: list[SearchResult] = []
        for item in items:
            if self.mode == "images":
                url = item.get("contentUrl") or item.get("hostPageUrl")
                results.append(
                    SearchResult(
                        title=item.get("name", ""),
                        url=url or "",
                        source=item.get("hostPageDisplayUrl", ""),
                        image_url=item.get("contentUrl"),
                        thumbnail_url=item.get("thumbnailUrl"),
                    )
                )
            elif self.mode == "videos":
                results.append(
                    SearchResult(
                        title=item.get("name", ""),
                        url=item.get("contentUrl") or item.get("hostPageUrl", ""),
                        source=item.get("publisher", [{}])[0].get("name", "")
                        if item.get("publisher")
                        else "",
                        description=item.get("description", ""),
                        thumbnail_url=item.get("thumbnailUrl"),
                        duration=item.get("duration", ""),
                    )
                )
            else:
                date = item.get("datePublished", "")
                try:
                    date = parsedate_to_datetime(date).strftime("%Y-%m-%d")
                except (TypeError, ValueError, OverflowError):
                    date = date[:10] if date else ""
                provider = item.get("provider", [{}])
                results.append(
                    SearchResult(
                        title=item.get("name", ""),
                        url=item.get("url", ""),
                        source=provider[0].get("name", "") if provider else "",
                        description=item.get("description", ""),
                        date=date,
                    )
                )
        total = int(response.get("totalEstimatedMatches", len(results)) or len(results))
        total_pages = max(1, min(10, (total + 7) // 8))
        return SearchPage(query, self.mode, page, total_pages, [r for r in results if r.url])
