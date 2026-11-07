# AGRO SEARCH ENGINE

**FAST • SMART • RELIABLE**

AGRO is a modular Telegram search bot with inline navigation for web, image,
news, video, map, book, shopping, research, weather, and URL metadata searches.
It uses live providers and explicitly reports unavailable features; it never
generates fake search results, prices, or availability.

## Project structure

```text
.
├── agro_search_engine/
│   ├── bot.py                    # Telegram commands, callbacks, and UX
│   ├── config.py                 # Environment-backed settings
│   ├── formatting.py             # Consistent HTML branding
│   ├── keyboards.py              # Inline keyboards and pagination
│   ├── models.py                 # Provider-neutral result models
│   ├── rate_limit.py             # In-memory per-user rate limiting
│   ├── service.py                # Provider registry / dependency boundary
│   ├── providers/
│   │   ├── base.py
│   │   ├── bing.py               # Images, news, videos
│   │   ├── books.py              # Google Books
│   │   ├── google_maps.py        # Google Places API
│   │   ├── research.py           # Semantic Scholar
│   │   ├── shopping.py           # SerpApi Google Shopping
│   │   ├── tavily.py             # Tavily web search
│   │   ├── url_inspector.py      # Safe URL metadata inspection
│   │   └── weather.py             # OpenWeather
│   └── utils/
│       ├── http.py               # Shared HTTP errors and client
│       └── url.py                # SSRF-aware public URL validation
├── .env.example
├── Dockerfile
├── requirements.txt
└── run.py
```

## Provider matrix

| Feature | Provider | Required variable |
|---|---|---|
| Web Search | Bing Web Search, with Tavily as fallback | `BING_SEARCH_API_KEY` or `TAVILY_API_KEY` |
| Image Search | Bing Image Search | `BING_SEARCH_API_KEY` |
| News | Bing News Search | `BING_SEARCH_API_KEY` |
| Videos | Bing Video Search | `BING_SEARCH_API_KEY` |
| Maps & Places | Google Places API (New) | `GOOGLE_MAPS_API_KEY` |
| Books | Google Books API | None |
| Shopping | SerpApi Google Shopping | `SERPAPI_API_KEY` |
| Research | Semantic Scholar | None |
| Weather | OpenWeather current weather | `OPENWEATHER_API_KEY` |
| URL Search | Direct safe public URL inspection | None |

Provider endpoints are isolated behind `SearchProvider`, so an adapter can be
replaced without changing Telegram handlers or formatting.

## Local setup

1. Create a Telegram bot with [@BotFather](https://t.me/BotFather) and copy its
   token.
2. Create a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate       # Windows: .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:

   ```bash
   cp .env.example .env
   ```

   Put credentials in `.env`. Do not commit `.env`, paste keys into Telegram,
   or hard-code credentials in source code.

5. Start the bot:

   ```bash
   python run.py
   ```

6. Open the bot in Telegram and send `/start`.

## API setup notes

- **Bing**: create a Bing Search resource and use a key that supports the
  Bing Web, Image, News, and Video Search endpoints.
- **Google Maps**: enable Places API (New) and restrict the key to the needed
  API and deployment environments.
- **OpenWeather**: create an API key and enable current weather.
- **SerpApi**: create an account and use its API key for Google Shopping.
- **Tavily** is optional when Bing Web Search is configured. It is useful as a
  web-search fallback.
- Google Books and Semantic Scholar may have their own public quotas and
  provider-side throttling even without a key.

## Deployment

The bot uses Telegram long polling, which works on any host that can run a
long-lived Python process.

```bash
docker build -t agro-search-engine .
docker run --env-file .env --restart unless-stopped agro-search-engine
```

For a managed deployment, set the same environment variables in the host's
secret manager. Never expose them in client-side code or bot messages.

## Operational behavior

- Per-user rate limiting defaults to 15 requests per 60 seconds.
- Query input is capped at 300 characters.
- URL inspection accepts only public `http`/`https` hosts, rejects credentials,
  local/private addresses, limits redirects, and caps response size.
- Search results are escaped as Telegram HTML before display.
- Provider errors are logged server-side without leaking secrets or stack traces.
- Shopping prices and availability are displayed only when supplied by SerpApi.
- Pagination is provider-backed where the API exposes offsets; single-response
  providers correctly show a single page.

## Bot commands

`/start` `/search` `/images` `/news` `/videos` `/maps` `/books` `/shopping`
`/research` `/weather` `/url` `/help` `/settings` `/about`
