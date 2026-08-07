from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def account_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📲 Получить ссылку",
                    callback_data="account_subscription_link",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Продлить подписку",
                    callback_data="account_extend",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛠 Поддержка",
                    callback_data="account_support",
                )
            ],
        ]
    )