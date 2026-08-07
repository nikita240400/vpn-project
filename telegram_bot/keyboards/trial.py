from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def trial_success_keyboard(
    subscription_url: str,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Добавить подписку в Happ",
                    url=subscription_url,
                )
            ]
        ]
    )