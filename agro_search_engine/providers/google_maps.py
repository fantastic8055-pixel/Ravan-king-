from __future__ import annotations

from ..config import Settings
from ..models import SearchPage, SearchResult
from ..utils.http import HttpClient, ProviderUnavailable
from .base import SearchProvider


class GoogleMapsProvider(SearchProvider):
    mode = "maps"

    def __init__(self, settings: Settings, http: HttpClient) -> None:
        self.key = settings.google_maps_api_key
        self.http = http

    async def search(self, query: str, page: int = 1) -> SearchPage:
        if not self.key:
            raise ProviderUnavailable("GOOGLE_MAPS_API_KEY is not configured.")
        response = await self.http.request(
            "POST",
            "https://places.googleapis.com/v1/places:searchText",
            json={"textQuery": query, "pageSize": 10},
            headers={
                "X-Goog-Api-Key": self.key,
                "X-Goog-FieldMask": (
                    "places.displayName,places.formattedAddress,places.googleMapsUri,"
                    "places.rating,places.websiteUri"
                ),
            },
        )
        results = []
        for place in response.get("places", []):
            name = place.get("displayName", {}).get("text", "Unnamed place")
            address = place.get("formattedAddress", "")
            url = place.get("googleMapsUri") or place.get("websiteUri")
            if url:
                results.append(
                    SearchResult(
                        title=name,
                        url=url,
                        source=address,
                        description=(
                            f"Rating: {place['rating']}"
                            if place.get("rating") is not None
                            else ""
                        ),
                    )
                )
        return SearchPage(query, self.mode, 1, 1, results)
