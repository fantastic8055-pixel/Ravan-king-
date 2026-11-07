from __future__ import annotations

from .config import Settings
from .models import SearchPage, SearchResult
from .providers.base import SearchProvider
from .providers.bing import BingProvider
from .providers.books import GoogleBooksProvider
from .providers.google_maps import GoogleMapsProvider
from .providers.research import SemanticScholarProvider
from .providers.shopping import SerpApiShoppingProvider
from .providers.tavily import TavilyProvider
from .providers.url_inspector import UrlInspectorProvider
from .providers.weather import OpenWeatherProvider
from .utils.http import HttpClient


class SearchService:
    """Provider registry kept separate from Telegram handlers."""

    def __init__(self, settings: Settings) -> None:
        http = HttpClient(settings.http_timeout_seconds)
        self.providers: dict[str, SearchProvider] = {}

        if settings.bing_search_api_key:
            self.providers.update(
                {
                    "images": BingProvider(settings, http, "images"),
                    "news": BingProvider(settings, http, "news"),
                    "videos": BingProvider(settings, http, "videos"),
                }
            )
        if settings.tavily_api_key:
            self.providers["web"] = TavilyProvider(settings, http)
        if settings.bing_search_api_key:
            # Bing is also a paginated web provider when configured.
            self.providers["web"] = BingWebProvider(settings, http)

        self.providers.update(
            {
                "maps": GoogleMapsProvider(settings, http),
                "books": GoogleBooksProvider(http),
                "shopping": SerpApiShoppingProvider(settings, http),
                "research": SemanticScholarProvider(http),
                "weather": OpenWeatherProvider(settings, http),
                "url": UrlInspectorProvider(settings),
            }
        )

    async def search(self, mode: str, query: str, page: int = 1) -> SearchPage:
        provider = self.providers.get(mode)
        if not provider:
            from .utils.http import ProviderUnavailable

            raise ProviderUnavailable(f"{mode} is not configured.")
        return await provider.search(query, page)

    def configured(self, mode: str) -> bool:
        provider = self.providers.get(mode)
        if not provider:
            return False
        # Providers with optional keys expose a key-less instance; report those
        # as unavailable before making a network request.
        return not (
            mode in {"maps", "shopping", "weather"}
            and getattr(provider, "key", None) is None
        )


class BingWebProvider(BingProvider):
    mode = "web"

    def __init__(self, settings: Settings, http: HttpClient) -> None:
        super().__init__(settings, http, "web")

    async def search(self, query: str, page: int = 1) -> SearchPage:
        if not self.key:
            from .utils.http import ProviderUnavailable

            raise ProviderUnavailable("BING_SEARCH_API_KEY is not configured.")
        response = await self.http.request(
            "GET",
            f"{self.endpoint}/search",
            params={
                "q": query,
                "count": 8,
                "offset": (page - 1) * 8,
                "safeSearch": "Strict",
                "mkt": "en-US",
            },
            headers={"Ocp-Apim-Subscription-Key": self.key},
        )
        results = [
            SearchResult(
                title=item.get("name", ""),
                url=item.get("url", ""),
                source=item.get("displayUrl", ""),
                description=item.get("snippet", ""),
            )
            for item in response.get("webPages", {}).get("value", [])
            if item.get("url")
        ]
        total = int(
            response.get("webPages", {}).get("totalEstimatedMatches", len(results))
            or len(results)
        )
        return SearchPage(query, self.mode, page, max(1, min(10, (total + 7) // 8)), results)
