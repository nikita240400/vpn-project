import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from telegram_bot.config import PUBLIC_BASE_URL
from telegram_bot.keyboards.account import account_keyboard
from telegram_bot.keyboards.plans import plans_keyboard
from telegram_bot.services.backend import (
    BackendAPIError,
    get_account,
    get_plans,
)
from telegram_bot.keyboards.checkout import checkout_keyboard
from telegram_bot.texts.checkout import build_checkout_text
from telegram_bot.texts.account import build_account_text
from telegram_bot.texts.plans import build_plans_text
from telegram_bot.texts.trial import build_trial_success_text

router = Router()
logger = logging.getLogger(__name__)


async def show_account(
    telegram_id: int,
    username: str | None,
    message: Message,
) -> None:
    try:
        data = await get_account(
            telegram_id=telegram_id,
            username=username,
        )

        subscription = data.get("subscription")

        if subscription is None:
            await message.answer(
                "У вас пока нет активной подписки."
            )
            return

        await message.answer(
            build_account_text(subscription),
            reply_markup=account_keyboard(),
            parse_mode="HTML",
        )

    except BackendAPIError as error:
        logger.warning(
            "Account loading failed for Telegram user %s: %s",
            telegram_id,
            error,
        )

        await message.answer(
            "Не удалось загрузить личный кабинет. "
            "Попробуйте немного позже."
        )


@router.message(F.text == "/account")
async def account_command(message: Message) -> None:
    await show_account(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        message=message,
    )


@router.callback_query(F.data == "account_subscription_link")
async def account_subscription_link(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    if callback.message is None:
        return

    try:
        data = await get_account(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
        )

        subscription = data.get("subscription")

        if subscription is None:
            await callback.message.answer(
                "У вас пока нет подписки."
            )
            return

        public_token = subscription.get("public_token")

        if not public_token:
            raise BackendAPIError(
                "Backend не вернул токен подписки"
            )

        subscription_url = (
            f"{PUBLIC_BASE_URL}/sub/{public_token}"
        )

        await callback.message.answer(
            build_trial_success_text(subscription_url),
            parse_mode="HTML",
        )

    except BackendAPIError as error:
        logger.warning(
            "Subscription link loading failed "
            "for Telegram user %s: %s",
            callback.from_user.id,
            error,
        )

        await callback.message.answer(
            "Не удалось получить ссылку. "
            "Попробуйте немного позже."
        )

@router.callback_query(F.data == "account_extend")
async def account_extend(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    if callback.message is None:
        return

    try:
        plans = await get_plans()

        paid_plans = [
            plan
            for plan in plans
            if plan.get("is_active")
            and float(plan.get("price", 0)) > 0
        ]

        if not paid_plans:
            await callback.message.edit_text(
                "Сейчас нет доступных тарифов для продления.",
                reply_markup=account_keyboard(),
            )
            return

        await callback.message.edit_text(
            build_plans_text(paid_plans),
            reply_markup=plans_keyboard(paid_plans),
            parse_mode="HTML",
        )

    except BackendAPIError as error:
        logger.warning(
            "Plans loading failed for Telegram user %s: %s",
            callback.from_user.id,
            error,
        )

        await callback.message.answer(
            "Не удалось загрузить тарифы. "
            "Попробуйте немного позже."
        )

@router.callback_query(F.data == "back_to_account")
async def back_to_account(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    if callback.message is None:
        return

    try:
        data = await get_account(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
        )

        subscription = data.get("subscription")

        if subscription is None:
            await callback.message.edit_text(
                "У вас пока нет подписки."
            )
            return

        await callback.message.edit_text(
            build_account_text(subscription),
            reply_markup=account_keyboard(),
            parse_mode="HTML",
        )

    except BackendAPIError as error:
        logger.warning(
            "Account return failed for Telegram user %s: %s",
            callback.from_user.id,
            error,
        )

        await callback.message.answer(
            "Не удалось открыть личный кабинет. "
            "Попробуйте немного позже."
        )

@router.callback_query(F.data.startswith("select_plan:"))
async def select_plan(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    if callback.message is None:
        return

    try:
        plan_id = int(
            callback.data.split(":", maxsplit=1)[1]
        )

        plans = await get_plans()

        plan = next(
            (
                item
                for item in plans
                if item.get("id") == plan_id
                and item.get("is_active")
                and float(item.get("price", 0)) > 0
            ),
            None,
        )

        if plan is None:
            await callback.message.edit_text(
                "Этот тариф сейчас недоступен.",
                reply_markup=account_keyboard(),
            )
            return

        await callback.message.edit_text(
            build_checkout_text(plan),
            reply_markup=checkout_keyboard(
                plan_id=plan["id"],
                price=plan["price"],
            ),
            parse_mode="HTML",
        )

    except (TypeError, ValueError):
        logger.warning(
            "Invalid plan callback from Telegram user %s: %s",
            callback.from_user.id,
            callback.data,
        )

        await callback.message.answer(
            "Не удалось определить выбранный тариф."
        )

    except BackendAPIError as error:
        logger.warning(
            "Plan loading failed for Telegram user %s: %s",
            callback.from_user.id,
            error,
        )

        await callback.message.answer(
            "Не удалось загрузить тариф. "
            "Попробуйте немного позже."
        )