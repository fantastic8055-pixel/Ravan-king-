from __future__ import annotations

import logging
from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .config import Settings
from .formatting import BRAND, home_text, page_header, prompt_for, result_text
from .keyboards import home_keyboard, navigation_keyboard, result_keyboard
from .models import SearchPage
from .rate_limit import RateLimiter
from .service import SearchService
from .utils.http import ProviderError, ProviderUnavailable
from .utils.url import is_safe_public_url

logger = logging.getLogger(__name__)


MODES = (
    "web",
    "images",
    "news",
    "videos",
    "maps",
    "books",
    "shopping",
    "research",
    "weather",
    "url",
)


def _setup_text(service: SearchService | None = None) -> str:
    status = ""
    if service:
        names = {
            "web": "Web",
            "images": "Images",
            "news": "News",
            "videos": "Videos",
            "maps": "Maps",
            "books": "Books",
            "shopping": "Shopping",
            "research": "Research",
            "weather": "Weather",
            "url": "URL",
        }
        status = "\n\n<b>Provider status</b>\n" + "\n".join(
            f"{'✅' if service.configured(mode) else '⚪'} {label}"
            for mode, label in names.items()
        )
    return (
        f"{BRAND}\n\n"
        "⚙️ <b>Settings</b>\n\n"
        "AGRO uses the API credentials configured by the bot operator. "
        "Your searches are sent only to the selected provider.\n\n"
        "Use /help for commands and provider setup details."
        f"{status}"
    )


def _about_text() -> str:
    return (
        f"{BRAND}\n\n"
        "🔎 <i>Search Smarter. Discover More.</i>\n\n"
        "AGRO is an all-in-one search assistant for web, images, news, "
        "videos, places, books, shopping, research, weather, and URL details.\n\n"
        "<b>FAST • SMART • RELIABLE</b>\n"
        "Results come from live providers. If a provider is not configured, "
        "AGRO says so instead of making results up."
    )


def _help_text() -> str:
    return (
        f"{BRAND}\n\n"
        "<b>Commands</b>\n"
        "/start — Open AGRO Search Engine\n"
        "/search — Web Search\n"
        "/images — Image Search\n"
        "/news — News Search\n"
        "/videos — Video Search\n"
        "/maps — Maps & Places\n"
        "/books — Book Search\n"
        "/shopping — Shopping Search\n"
        "/research — Research Search\n"
        "/weather — Weather\n"
        "/url — URL Search\n"
        "/settings — Settings\n"
        "/about — About AGRO\n"
        "/help — This help\n\n"
        "Choose a category, send one query, and use the inline buttons to open "
        "a result or move through pages."
    )


def _mode_from_command(command: str) -> str | None:
    return {
        "search": "web",
        "images": "images",
        "news": "news",
        "videos": "videos",
        "maps": "maps",
        "books": "books",
        "shopping": "shopping",
        "research": "research",
        "weather": "weather",
        "url": "url",
    }.get(command)


async def _show_mode(
    update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str
) -> None:
    context.user_data["mode"] = mode
    if update.callback_query:
        await update.callback_query.edit_message_text(
            prompt_for(mode),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[
                    # Re-open the category without adding a new message.
                    InlineKeyboardButton("🏠 Home", callback_data="home")
                ]]
            ),
        )
    elif update.effective_message:
        await update.effective_message.reply_text(
            prompt_for(mode),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("🏠 Home", callback_data="home")
                ]]
            ),
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.effective_message.reply_text(
        home_text(), parse_mode=ParseMode.HTML, reply_markup=home_keyboard()
    )


async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    command = update.effective_message.text.split()[0].lstrip("/").split("@")[0]
    if command == "help":
        await update.effective_message.reply_text(
            _help_text(), parse_mode=ParseMode.HTML, reply_markup=home_keyboard()
        )
    elif command == "settings":
        await update.effective_message.reply_text(
            _setup_text(context.application.bot_data["search_service"]),
            parse_mode=ParseMode.HTML,
            reply_markup=home_keyboard(),
        )
    elif command == "about":
        await update.effective_message.reply_text(
            _about_text(), parse_mode=ParseMode.HTML, reply_markup=home_keyboard()
        )
    else:
        mode = _mode_from_command(command)
        if mode:
            await _show_mode(update, context, mode)


async def _send_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    page: SearchPage,
) -> None:
    chat_id = update.effective_chat.id
    if not page.results:
        await context.bot.send_message(
            chat_id=chat_id,
            text=page_header(page) + "\nNo results found for this query.",
            parse_mode=ParseMode.HTML,
            reply_markup=navigation_keyboard(page.mode, page.page, page.total_pages),
        )
        return

    await context.bot.send_message(
        chat_id=chat_id,
        text=page_header(page),
        parse_mode=ParseMode.HTML,
    )
    for index, item in enumerate(page.results, start=1):
        text = result_text(item, index, page.mode)
        markup = result_keyboard(item.url) if is_safe_public_url(item.url) else None
        if page.mode == "images" and item.image_url and is_safe_public_url(item.image_url):
            try:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=item.image_url,
                    caption=text[:1024],
                    parse_mode=ParseMode.HTML,
                    reply_markup=markup,
                )
                continue
            except Exception:
                logger.info("Image preview failed; sending text card", exc_info=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=markup,
            disable_web_page_preview=True,
        )
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Page {page.page} of {page.total_pages}",
        reply_markup=navigation_keyboard(page.mode, page.page, page.total_pages),
    )


async def _perform_search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    mode: str,
    query: str,
    page_number: int = 1,
) -> None:
    service: SearchService = context.application.bot_data["search_service"]
    limiter: RateLimiter = context.application.bot_data["rate_limiter"]
    user_id = update.effective_user.id
    if not limiter.allow(user_id):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⏳ You’re searching too quickly. Please try again in a moment.",
        )
        return
    if len(query) > context.application.bot_data["settings"].max_query_length:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ Please keep your query under 300 characters.",
        )
        return
    if mode == "url" and not is_safe_public_url(query):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ Send a valid public URL beginning with http:// or https://.",
        )
        return
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing",
    )
    try:
        result_page = await service.search(mode, query, page_number)
        context.user_data["last_query"] = query
        context.user_data["last_mode"] = mode
        context.user_data["last_page"] = page_number
        await _send_page(update, context, result_page)
    except ProviderUnavailable as exc:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                f"⚙️ <b>{escape(mode.title())} is unavailable</b>\n\n"
                f"{escape(str(exc))}\n\n"
                "The bot operator can enable this provider through environment variables."
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=home_keyboard(),
        )
    except (ProviderError, ValueError) as exc:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"⚠️ I couldn’t complete that search safely.\n\n{escape(str(exc))}",
            parse_mode=ParseMode.HTML,
            reply_markup=home_keyboard(),
        )
    except Exception:
        logger.exception("Unhandled provider error for mode=%s", mode)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ The provider is temporarily unavailable. Please try again later.",
            reply_markup=home_keyboard(),
        )


async def text_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mode = context.user_data.get("mode")
    if mode not in MODES:
        await update.effective_message.reply_text(
            "Choose a search category first.", reply_markup=home_keyboard()
        )
        return
    query = update.effective_message.text.strip()
    if not query:
        await update.effective_message.reply_text(prompt_for(mode), parse_mode=ParseMode.HTML)
        return
    await _perform_search(update, context, mode, query)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    if data == "noop":
        return
    if data == "home":
        context.user_data.clear()
        await query.edit_message_text(
            home_text(), parse_mode=ParseMode.HTML, reply_markup=home_keyboard()
        )
        return
    if data == "settings":
        await query.edit_message_text(
            _setup_text(context.application.bot_data["search_service"]),
            parse_mode=ParseMode.HTML,
            reply_markup=home_keyboard(),
        )
        return
    if data == "about":
        await query.edit_message_text(
            _about_text(), parse_mode=ParseMode.HTML, reply_markup=home_keyboard()
        )
        return
    if data.startswith("mode:"):
        await _show_mode(update, context, data.split(":", 1)[1])
        return
    if data.startswith("page:"):
        _, mode, page = data.split(":", 2)
        if mode not in MODES:
            return
        last_query = context.user_data.get("last_query")
        if not last_query:
            await query.edit_message_text(
                "This result session has expired. Start a new search.",
                reply_markup=home_keyboard(),
            )
            return
        await query.edit_message_text("🔄 Loading results...")
        await _perform_search(update, context, mode, last_query, int(page))


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Telegram update error", exc_info=context.error)


def build_application(settings: Settings) -> Application:
    application = Application.builder().token(settings.telegram_bot_token).build()
    application.bot_data["settings"] = settings
    application.bot_data["search_service"] = SearchService(settings)
    application.bot_data["rate_limiter"] = RateLimiter(
        settings.rate_limit_requests, settings.rate_limit_window_seconds
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        CommandHandler(
            [
                "search",
                "images",
                "news",
                "videos",
                "maps",
                "books",
                "shopping",
                "research",
                "weather",
                "url",
                "help",
                "settings",
                "about",
            ],
            command_handler,
        )
    )
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_query)
    )
    application.add_error_handler(error_handler)
    return application


def main() -> None:
    settings = Settings.from_env()
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logger.info("Starting AGRO Search Engine")
    build_application(settings).run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
