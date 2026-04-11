import logging
from datetime import datetime

import aiohttp

logger = logging.getLogger(__name__)


async def fetch_currency_data():
    """Получает данные о курсах валют с API ЦБ РФ."""
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json(content_type=None)
                logging.warning(f"CBR API error: {response.status}")
    except Exception as e:
        logging.error(f"CBR fetch error: {e}")
    return None


def format_currency_message(data) -> str:
    """Форматирует JSON от ЦБ в красивое сообщение."""
    if not data:
        return "🚨 Не удалось получить данные о курсах валют."

    valutes = data.get("Valute", {})
    target_codes = ["USD", "EUR", "CNY", "HKD", "BYN", "KZT"]
    lines = [
        f"<b>📊 Курсы валют ЦБ РФ на {datetime.now().strftime('%d.%m')}</b>\n"
    ]

    for code in target_codes:
        v = valutes.get(code)
        if not v:
            continue
        name = v["Name"]
        value = v["Value"]
        previous = v["Previous"]
        nominal = v["Nominal"]
        diff = value - previous
        trend = "🔺" if diff > 0 else "🔻"
        nominal_str = f"{nominal} {code}" if nominal > 1 else code
        lines.append(
            f"• {name} ({nominal_str}): <b>{value:.2f}₽</b> "
            f"{trend} <i>({diff:+.2f})</i>"
        )

    lines.append("\n<i>Данные обновляются по рабочим дням ЦБ РФ</i>")
    return "\n".join(lines)


async def get_currency_rates():
    """Основная функция для вызова извне."""
    data = await fetch_currency_data()
    return format_currency_message(data)
