from __future__ import annotations

from ..models import SearchPage, SearchResult
from ..utils.http import HttpClient
from .base import SearchProvider


class SemanticScholarProvider(SearchProvider):
    mode = "research"

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    async def search(self, query: str, page: int = 1) -> SearchPage:
        response = await self.http.request(
            "GET",
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={
                "query": query,
                "limit": 10,
                "offset": (page - 1) * 10,
                "fields": "title,abstract,authors,year,url,venue",
            },
        )
        results = []
        for item in response.get("data", []):
            authors = ", ".join(
                author.get("name", "")
                for author in item.get("authors", [])[:4]
                if author.get("name")
            )
            url = item.get("url")
            if url:
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=url,
                        author=authors,
                        source=item.get("venue", ""),
                        date=str(item.get("year", "")) if item.get("year") else "",
                        description=item.get("abstract", "") or "",
                    )
                )
        total = int(response.get("total", len(results)) or len(results))
        return SearchPage(query, self.mode, page, max(1, min(10, (total + 9) // 10)), results)
