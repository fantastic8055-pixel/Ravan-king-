from __future__ import annotations

from typing import Any

import httpx


class ProviderUnavailable(Exception):
    """Raised when a provider has no configured credentials or is unavailable."""


class ProviderError(Exception):
    """Raised for a provider response that cannot be used safely."""


class HttpClient:
    def __init__(self, timeout_seconds: float) -> None:
        self.timeout = httpx.Timeout(timeout_seconds, connect=5.0)

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=False,
                headers={"User-Agent": "AGRO-Search-Engine/1.0"},
            ) as client:
                response = await client.request(
                    method, url, params=params, json=json, headers=headers
                )
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderError(f"HTTP provider request failed: {exc}") from exc
