from __future__ import annotations

from ..models import SearchPage, SearchResult
from ..utils.http import HttpClient
from .base import SearchProvider


class GoogleBooksProvider(SearchProvider):
    mode = "books"

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    async def search(self, query: str, page: int = 1) -> SearchPage:
        response = await self.http.request(
            "GET",
            "https://www.googleapis.com/books/v1/volumes",
            params={"q": query, "maxResults": 10, "startIndex": (page - 1) * 10},
        )
        results = []
        for item in response.get("items", []):
            info = item.get("volumeInfo", {})
            identifiers = info.get("industryIdentifiers", [])
            link = info.get("infoLink") or (
                f"https://books.google.com/books?id={item.get('id')}"
                if item.get("id")
                else ""
            )
            if link:
                results.append(
                    SearchResult(
                        title=info.get("title", ""),
                        url=link,
                        author=", ".join(info.get("authors", [])),
                        description=info.get("description", ""),
                        source=info.get("publisher", ""),
                        image_url=(info.get("imageLinks") or {}).get("thumbnail"),
                    )
                )
        total = int(response.get("totalItems", len(results)) or len(results))
        return SearchPage(query, self.mode, page, max(1, min(10, (total + 9) // 10)), results)
