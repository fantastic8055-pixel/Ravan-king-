from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔎 Web Search", callback_data="mode:web"),
                InlineKeyboardButton("🖼 Images", callback_data="mode:images"),
            ],
            [
                InlineKeyboardButton("📰 News", callback_data="mode:news"),
                InlineKeyboardButton("🎬 Videos", callback_data="mode:videos"),
            ],
            [
                InlineKeyboardButton("📍 Maps", callback_data="mode:maps"),
                InlineKeyboardButton("📚 Books", callback_data="mode:books"),
            ],
            [
                InlineKeyboardButton("🛒 Shopping", callback_data="mode:shopping"),
                InlineKeyboardButton("🎓 Research", callback_data="mode:research"),
            ],
            [InlineKeyboardButton("🌦 Weather", callback_data="mode:weather")],
            [InlineKeyboardButton("🔗 URL Search", callback_data="mode:url")],
            [
                InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
                InlineKeyboardButton("ℹ️ About", callback_data="about"),
            ],
        ]
    )


def navigation_keyboard(
    mode: str, page: int, total_pages: int
) -> InlineKeyboardMarkup:
    buttons: list[InlineKeyboardButton] = []
    if page > 1:
        buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"page:{mode}:{page - 1}"))
    buttons.append(
        InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop")
    )
    if page < total_pages:
        buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"page:{mode}:{page + 1}"))
    return InlineKeyboardMarkup(
        [
            buttons,
            [
                InlineKeyboardButton("🏠 Home", callback_data="home"),
                InlineKeyboardButton("🔙 Back", callback_data=f"mode:{mode}"),
            ],
        ]
    )


def result_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Open Result", url=url)]])
