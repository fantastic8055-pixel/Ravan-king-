from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    tavily_api_key: str | None
    bing_search_api_key: str | None
    bing_search_endpoint: str
    google_maps_api_key: str | None
    openweather_api_key: str | None
    serpapi_api_key: str | None
    log_level: str
    rate_limit_requests: int
    rate_limit_window_seconds: int
    http_timeout_seconds: float
    max_query_length: int
    max_url_response_bytes: int

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN is missing. Copy .env.example to .env and configure it."
            )

        def integer(name: str, default: int) -> int:
            try:
                return int(os.getenv(name, str(default)))
            except ValueError:
                return default

        def number(name: str, default: float) -> float:
            try:
                return float(os.getenv(name, str(default)))
            except ValueError:
                return default

        return cls(
            telegram_bot_token=token,
            tavily_api_key=os.getenv("TAVILY_API_KEY") or None,
            bing_search_api_key=os.getenv("BING_SEARCH_API_KEY") or None,
            bing_search_endpoint=os.getenv(
                "BING_SEARCH_ENDPOINT",
                "https://api.bing.microsoft.com/v7.0",
            ).rstrip("/"),
            google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY") or None,
            openweather_api_key=os.getenv("OPENWEATHER_API_KEY") or None,
            serpapi_api_key=os.getenv("SERPAPI_API_KEY") or None,
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            rate_limit_requests=max(1, integer("RATE_LIMIT_REQUESTS", 15)),
            rate_limit_window_seconds=max(1, integer("RATE_LIMIT_WINDOW_SECONDS", 60)),
            http_timeout_seconds=max(3.0, number("HTTP_TIMEOUT_SECONDS", 15)),
            max_query_length=max(20, integer("MAX_QUERY_LENGTH", 300)),
            max_url_response_bytes=max(
                100_000, integer("MAX_URL_RESPONSE_BYTES", 500_000)
            ),
        )
