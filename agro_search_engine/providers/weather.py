from __future__ import annotations

from ..config import Settings
from ..models import SearchPage, SearchResult
from ..utils.http import HttpClient, ProviderUnavailable
from .base import SearchProvider


class OpenWeatherProvider(SearchProvider):
    mode = "weather"

    def __init__(self, settings: Settings, http: HttpClient) -> None:
        self.key = settings.openweather_api_key
        self.http = http

    async def search(self, query: str, page: int = 1) -> SearchPage:
        if not self.key:
            raise ProviderUnavailable("OPENWEATHER_API_KEY is not configured.")
        response = await self.http.request(
            "GET",
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": query, "appid": self.key, "units": "metric"},
        )
        main = response.get("main", {})
        weather = response.get("weather", [{}])[0]
        wind = response.get("wind", {})
        description = (
            f"{weather.get('description', '').capitalize()}\n"
            f"Temperature: {main.get('temp', 'N/A')}°C\n"
            f"Feels like: {main.get('feels_like', 'N/A')}°C\n"
            f"Humidity: {main.get('humidity', 'N/A')}%\n"
            f"Wind: {wind.get('speed', 'N/A')} m/s"
        )
        result = SearchResult(
            title=f"{response.get('name', query)} weather",
            url=f"https://openweathermap.org/city/{response.get('id', '')}",
            source=response.get("sys", {}).get("country", ""),
            description=description,
        )
        return SearchPage(query, self.mode, 1, 1, [result])
