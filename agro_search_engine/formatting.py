from __future__ import annotations

from html import escape

from .models import SearchPage, SearchResult


BRAND = "🌐 <b>AGRO SEARCH ENGINE</b>"


def home_text() -> str:
    return (
        f"{BRAND}\n\n"
        "🔎 <i>Search Smarter. Discover More.</i>\n\n"
        "Choose what you want to search:"
    )


def prompt_for(mode: str) -> str:
    prompts = {
        "web": "🔎 <b>Web Search</b>\nSend a search query.",
        "images": "🖼 <b>Image Search</b>\nWhat image should I find?",
        "news": "📰 <b>News Search</b>\nSend a topic or headline.",
        "videos": "🎬 <b>Video Search</b>\nWhat video are you looking for?",
        "maps": "📍 <b>Maps & Places</b>\nSearch a city, business, place, or address.",
        "books": "📚 <b>Book Search</b>\nSend a title, author, or topic.",
        "shopping": "🛒 <b>Shopping Search</b>\nWhat product are you looking for?",
        "research": "🎓 <b>Research Search</b>\nSearch papers, documentation, or learning material.",
        "weather": "🌦 <b>Weather</b>\nSend a city name.",
        "url": "🔗 <b>URL Search</b>\nSend a complete URL beginning with http:// or https://.",
    }
    return prompts.get(mode, "Send a search query.")


def _line(label: str, value: str) -> str:
    return f"\n<b>{escape(label)}:</b> {escape(value)}" if value else ""


def result_text(result: SearchResult, index: int, mode: str) -> str:
    title = escape(result.title or "Untitled result")
    body = f"<b>{index}. {title}</b>"
    if result.source:
        body += _line("Source", result.source)
    if result.author:
        body += _line("Author", result.author)
    if result.store:
        body += _line("Store", result.store)
    if result.price:
        body += _line("Price", result.price)
    if result.date:
        body += _line("Date", result.date)
    if result.duration:
        body += _line("Duration", result.duration)
    if result.description:
        description = result.description.strip()
        if len(description) > 500:
            description = f"{description[:497]}..."
        body += f"\n\n{escape(description)}"
    if mode != "url" and result.url:
        body += f"\n\n<code>{escape(result.url)}</code>"
    return body


def page_header(page: SearchPage) -> str:
    labels = {
        "web": "Web Results",
        "images": "Image Results",
        "news": "News Results",
        "videos": "Video Results",
        "maps": "Places",
        "books": "Books",
        "shopping": "Shopping Results",
        "research": "Research Results",
        "weather": "Weather",
        "url": "URL Information",
    }
    return (
        f"{BRAND}\n"
        f"📌 <b>{labels.get(page.mode, 'Results')}</b> for "
        f"<i>{escape(page.query)}</i>\n"
    )
