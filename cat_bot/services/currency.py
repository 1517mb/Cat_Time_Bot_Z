import asyncio
import logging
from datetime import datetime

import aiohttp

logger = logging.getLogger(__name__)

FLAGS = {
    "USD": "🇺🇸",
    "EUR": "🇪🇺",
    "CNY": "🇨🇳",
    "HKD": "🇭🇰",
    "BYN": "🇧🇾",
    "KZT": "🇰🇿"
}


async def fetch_currency_data():
    """Получает данные о курсах валют с API ЦБ РФ."""
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json(content_type=None)
                logger.warning(
                    "CBR API returned HTTP %s", response.status,
                    extra={"provider": "cbr", "operation": "fetch_currency"},
                )
    except (aiohttp.ClientError, asyncio.TimeoutError) as error:
        logger.warning(
            "CBR request failed (%s): %s", type(error).__name__, error,
            extra={"provider": "cbr", "operation": "fetch_currency"},
        )
    except Exception:
        logger.exception(
            "Unexpected error fetching CBR data",
            extra={"provider": "cbr", "operation": "fetch_currency"},
        )
    return None


def format_currency_message(data: dict | None) -> str:
    """Форматирует JSON от ЦБ в красивое сообщение."""
    if not data:
        return "🚨 Не удалось получить данные о курсах валют."

    valutes = data.get("Valute", {})
    target_codes = ["USD", "EUR", "CNY", "HKD", "BYN", "KZT"]
    date_str = datetime.now().strftime('%d.%m.%Y')
    lines = [f"<b>📊 Курсы валют ЦБ РФ на {date_str}</b>\n"]

    for code in target_codes:
        v = valutes.get(code)
        if not v:
            continue
        name = v["Name"]
        value = v["Value"]
        previous = v["Previous"]
        nominal = v["Nominal"]
        diff = value - previous
        if diff > 0:
            trend = "🟢"
        elif diff < 0:
            trend = "🔴"
        else:
            trend = "➖"

        nominal_str = f"{nominal} {code}" if nominal > 1 else code
        flag = FLAGS.get(code, "🪙")
        lines.append(
            f"{flag} {name} ({nominal_str}): <b>{value:.2f} ₽</b> "
            f"{trend} <i>({diff:+.2f})</i>"
        )

    lines.append("\n<i>🔄 Данные обновляются по рабочим дням ЦБ РФ</i>")
    return "\n".join(lines)


async def get_currency_rates():
    """Основная функция для вызова извне."""
    data = await fetch_currency_data()
    return format_currency_message(data)
