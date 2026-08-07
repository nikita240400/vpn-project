from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def plans_keyboard(
    plans: list[dict],
) -> InlineKeyboardMarkup:
    rows = []

    for plan in plans:
        rows.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"{plan['name']} — "
                        f"{plan['days']} дней / "
                        f"{plan['price']} ₽"
                    ),
                    callback_data=f"select_plan:{plan['id']}",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="back_to_account",
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=rows,
    )