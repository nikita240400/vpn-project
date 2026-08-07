from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def activation_keyboard(platform: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Активировать 3 дня",
                    callback_data=f"activate_trial:{platform}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=f"back_to_happ:{platform}",
                )
            ],
        ]
    )