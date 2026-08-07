def build_plans_text(plans: list[dict]) -> str:
    lines = [
        "🍩 <b>Продление подписки</b>",
        "",
        "Выберите подходящий тариф:",
        "",
    ]

    for plan in plans:
        price = f"{plan['price']} ₽"
        days = plan["days"]

        lines.append(
            f"• <b>{plan['name']}</b>\n"
            f"⏳ {days} дней — 💳 {price}"
        )

    lines.extend(
        [
            "",
            "👇 Нажмите на нужный тариф.",
        ]
    )

    return "\n".join(lines)