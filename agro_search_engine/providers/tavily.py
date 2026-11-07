from __future__ import annotations

from ..config import Settings
from ..models import SearchPage, SearchResult
from ..utils.http import HttpClient, ProviderError, ProviderUnavailable
from .base import SearchProvider


class TavilyProvider(SearchProvider):
    mode = "web"

    def __init__(self, settings: Settings, http: HttpClient) -> None:
        self.key = settings.tavily_api_key
        self.http = http

    async def search(self, query: str, page: int = 1) -> SearchPage:
        if not self.key:
            raise ProviderUnavailable("TAVILY_API_KEY is not configured.")
        response = await self.http.request(
            "POST",
            "https://api.tavily.com/search",
            json={
                "api_key": self.key,
                "query": query,
                "search_depth": "basic",
                "max_results": 8,
                "include_answer": False,
                "include_raw_content": False,
            },
        )
        results = [
            SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                description=item.get("content", ""),
                source=item.get("url", "").split("/")[2]
                if "://" in item.get("url", "")
                else "",
            )
            for item in response.get("results", [])
            if item.get("url")
        ]
        return SearchPage(query, self.mode, 1, 1, results)
