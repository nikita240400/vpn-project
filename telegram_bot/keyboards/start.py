from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


CHANNEL_URL = "https://t.me/vpn_ponchik"


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Подписаться на канал",
                    url=CHANNEL_URL,
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Я подписался",
                    callback_data="check_channel_subscription",
                )
            ],
        ]
    )
