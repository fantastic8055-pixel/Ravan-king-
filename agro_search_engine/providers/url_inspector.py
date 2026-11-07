from __future__ import annotations

from html import unescape
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from ..config import Settings
from ..models import SearchPage, SearchResult
from ..utils.url import is_safe_public_url
from .base import SearchProvider


class UrlInspectorProvider(SearchProvider):
    mode = "url"

    def __init__(self, settings: Settings) -> None:
        self.timeout = settings.http_timeout_seconds
        self.max_bytes = settings.max_url_response_bytes

    async def search(self, query: str, page: int = 1) -> SearchPage:
        url = query.strip()
        if not is_safe_public_url(url):
            raise ValueError(
                "That URL is not a valid safe public HTTP/HTTPS address."
            )
        current = url
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout, connect=5.0),
            follow_redirects=False,
            headers={"User-Agent": "AGRO-Search-Engine/1.0"},
        ) as client:
            response = None
            for _ in range(3):
                response = await client.get(current)
                if response.is_redirect:
                    target = urljoin(current, response.headers.get("location", ""))
                    if not is_safe_public_url(target):
                        raise ValueError("The website redirected to an unsafe URL.")
                    current = target
                    continue
                break
            if response is None:
                raise ValueError("The website did not return a response.")
            response.raise_for_status()
            if int(response.headers.get("content-length", "0") or 0) > self.max_bytes:
                raise ValueError("The website response is too large to inspect safely.")
            content = response.content[: self.max_bytes]
        content_type = response.headers.get("content-type", "")
        title = current
        description = ""
        if "html" in content_type:
            soup = BeautifulSoup(content, "html.parser")
            title = soup.title.get_text(" ", strip=True) if soup.title else current
            tag = soup.find("meta", attrs={"name": "description"})
            if tag and tag.get("content"):
                description = unescape(tag["content"].strip())
            elif soup.get_text(" ", strip=True):
                description = soup.get_text(" ", strip=True)[:500]
        host = current.split("//", 1)[-1].split("/", 1)[0]
        result = SearchResult(
            title=title,
            url=current,
            source=host,
            description=description or f"HTTP {response.status_code} · {content_type or 'unknown content type'}",
        )
        return SearchPage(query, self.mode, 1, 1, [result])
