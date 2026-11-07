from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SearchResult:
    title: str
    url: str
    description: str = ""
    source: str = ""
    date: str = ""
    image_url: str | None = None
    thumbnail_url: str | None = None
    author: str = ""
    price: str = ""
    store: str = ""
    duration: str = ""


@dataclass
class SearchPage:
    query: str
    mode: str
    page: int
    total_pages: int
    results: list[SearchResult] = field(default_factory=list)
    unavailable_reason: str = ""
