import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from telegram_bot.config import PUBLIC_BASE_URL
from telegram_bot.keyboards.activation import activation_keyboard
from telegram_bot.keyboards.devices import happ_keyboard
from telegram_bot.keyboards.start import start_keyboard
from telegram_bot.services.backend import BackendAPIError, activate_trial
from telegram_bot.texts.activation import ACTIVATION_TEXT
from telegram_bot.texts.devices import DEVICE_SETUP_TEXT
from telegram_bot.texts.start import START_TEXT
from telegram_bot.texts.trial import (
    TRIAL_ACTIVATING_TEXT,
    TRIAL_ERROR_TEXT,
    build_trial_success_text,
)

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("device:"))
async def select_device(callback: CallbackQuery) -> None:
    platform = callback.data.split(":", maxsplit=1)[1]

    if callback.message is not None:
        await callback.message.edit_text(
            DEVICE_SETUP_TEXT,
            reply_markup=happ_keyboard(platform),
            parse_mode="HTML",
        )

    await callback.answer()


@router.callback_query(F.data.startswith("happ_installed:"))
async def happ_installed(callback: CallbackQuery) -> None:
    platform = callback.data.split(":", maxsplit=1)[1]

    if callback.message is not None:
        await callback.message.edit_text(
            ACTIVATION_TEXT,
            reply_markup=activation_keyboard(platform),
            parse_mode="HTML",
        )

    await callback.answer()


@router.callback_query(F.data.startswith("activate_trial:"))
async def activate_trial_access(callback: CallbackQuery) -> None:
    platform = callback.data.split(":", maxsplit=1)[1]

    await callback.answer()

    if callback.message is None:
        return

    await callback.message.edit_text(
        TRIAL_ACTIVATING_TEXT,
        parse_mode="HTML",
    )

    try:
        result = await activate_trial(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
        )

        public_token = result.get("public_token")

        if not public_token:
            raise BackendAPIError(
                "Backend не вернул токен подписки"
            )

        subscription_url = (
            f"{PUBLIC_BASE_URL}/sub/{public_token}"
        )

        await callback.message.edit_text(
            build_trial_success_text(subscription_url),
            parse_mode="HTML",
        )

    except BackendAPIError as error:
        logger.warning(
            "Trial activation failed for Telegram user %s: %s",
            callback.from_user.id,
            error,
        )

        await callback.message.edit_text(
            TRIAL_ERROR_TEXT,
            reply_markup=activation_keyboard(platform),
            parse_mode="HTML",
        )

    except Exception:
        logger.exception(
            "Unexpected trial activation error for Telegram user %s",
            callback.from_user.id,
        )

        await callback.message.edit_text(
            TRIAL_ERROR_TEXT,
            reply_markup=activation_keyboard(platform),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("back_to_happ:"))
async def back_to_happ(callback: CallbackQuery) -> None:
    platform = callback.data.split(":", maxsplit=1)[1]

    if callback.message is not None:
        await callback.message.edit_text(
            DEVICE_SETUP_TEXT,
            reply_markup=happ_keyboard(platform),
            parse_mode="HTML",
        )

    await callback.answer()


@router.callback_query(F.
data == "back_to_devices")
async def back_to_devices(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await callback.message.edit_text(
            START_TEXT,
            reply_markup=start_keyboard(),
            parse_mode="HTML",
        )

    await callback.answer()