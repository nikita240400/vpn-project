from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


HAPP_DOWNLOAD_URLS = {
    "ios": "https://apps.apple.com/app/id6504287215",
    "android": "https://play.google.com/store/apps/details?id=com.happproxy",
    "windows": "https://github.com/Happ-proxy/happ-desktop/releases/latest",
    "macos": "https://github.com/Happ-proxy/happ-desktop/releases/latest",
}


def happ_keyboard(platform: str) -> InlineKeyboardMarkup:
    download_url = HAPP_DOWNLOAD_URLS[platform]

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📲 Скачать Happ",
                    url=download_url,
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Уже установил",
                    callback_data=f"happ_installed:{platform}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="back_to_devices",
                )
            ],
        ]
    )