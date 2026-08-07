from pathlib import Path

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from telegram_bot.config import PUBLIC_BASE_URL
from telegram_bot.services.backend import (
    BackendAPIError,
    activate_trial,
)

router = Router()

WELCOME_IMAGE_PATH = (
    Path(__file__).resolve().parent.parent
    / "media"
    / "welcome.jpg"
)

CHANNEL_URL = "https://t.me/vpn_ponchik"
SUPPORT_URL = "https://t.me/ponchik_VPNbot"


WELCOME_TEXT = """
<b>Пончик VPN — 1+ год стабильной работы</b>

<blockquote>— ⚡ <b>До 25 Гбит/с</b>
— 🔑 <b>1 ключ — от 3 до 9 устройств</b>
— 💸 <b>Бонус 19RUB за каждого приглашенного друга</b>
— 🛡 <b>0% логов | Поддержка 12/7</b>
— 📢 <a href="https://t.me/vpn_ponchik">Наш канал</a></blockquote>

<i>Не тратим ваше время — подключение за 1 минуту</i>
Начиная использование бота/мини-приложения, вы соглашаетесь с условиями пользовательского соглашения:
— <b>Пользовательское соглашение:</b>
<a href="https://t.me/vpn_ponchik">Ознакомиться</a>
"""


def welcome_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧬 Пробная подписка",
                    callback_data="trial_subscription",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 Поддержка",
                    url=SUPPORT_URL,
                ),
                InlineKeyboardButton(
                    text="📢 Канал",
                    url=CHANNEL_URL,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🤝 О сервисе",
                    callback_data="about_service",
                )
            ],
        ]
    )


def trial_success_keyboard(
    public_token: str,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💻 Подключить устройство",
                    web_app=WebAppInfo(
                        url=(
                            f"{PUBLIC_BASE_URL}/happ/"
                            f"{public_token}"
                        )
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧬 Личный кабинет",
                    callback_data="back_to_account",
                )
            ],
        ]
    )


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer_photo(
        photo=FSInputFile(WELCOME_IMAGE_PATH),
        caption=WELCOME_TEXT,
        reply_markup=welcome_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "trial_subscription")
async def trial_subscription_handler(
    callback: CallbackQuery,
) -> None:
    if callback.message is None:
        await callback.answer()
        return

    try:
        data = await activate_trial(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
        )

        public_token = data["public_token"]

        subscription_url = (
            f"{PUBLIC_BASE_URL}/sub/{public_token}"
        )

        success_text = f"""
✅ <b>Подписка успешно создана: 🎉</b>

<code>{subscription_url}</code>

📦 <b>Информация о тарифе:</b>
<blockquote>🕒 Тариф: Пробный период
📊 Трафик: Безлимитный
📱 Лимит устройств: 3</blockquote>

<i>Добавьте подписку в приложение — это просто:</i>

📲 <b>Подключите устройство</b> через кнопку ниже — выберите вашу платформу (телефон, ТВ, ПК и т.д.) и следуйте простой инструкции.

💬 Если у вас возникнут вопросы, не стесняйтесь обращаться в поддержку.
"""

        await callback.message.edit_caption(
            caption=success_text,
            reply_markup=trial_success_keyboard(
                public_token=str(public_token),
            ),
            parse_mode="HTML",
        )

        await callback.answer(
            "Подписка успешно создана",
        )

    except BackendAPIError:
        await callback.answer(
"Не удалось создать подписку. "
            "Попробуйте немного позже.",
            show_alert=True,
        )

    except Exception:
        await callback.answer(
            "Произошла ошибка. Попробуйте немного позже.",
            show_alert=True,
        )
