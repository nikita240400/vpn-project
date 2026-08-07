from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def checkout_keyboard(
    plan_id: int,
    price: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"💳 Оплатить {price} ₽",
                    callback_data=f"pay_plan:{plan_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад к тарифам",
                    callback_data="account_extend",
                )
            ],
        ]
    )