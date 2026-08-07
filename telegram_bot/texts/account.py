from datetime import datetime


def build_account_text(subscription: dict) -> str:
    expires_at = datetime.fromisoformat(
        subscription["expires_at"]
    )

    expires_text = expires_at.strftime("%d.%m.%Y")

    status_text = (
        "🟢 Активна"
        if subscription["is_active"]
        else "🔴 Неактивна"
    )

    return f"""
🍩 <b>Пончик VPN</b>

{status_text}

📅 Действует до: <b>{expires_text}</b>
🌍 Серверов: <b>{subscription["server_count"]}</b>

Выберите действие:
"""