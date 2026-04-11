import logging
from datetime import datetime

import aiohttp

logger = logging.getLogger(__name__)


async def fetch_crypto_data():
    """Получает данные о крипте с CoinGecko (бесплатный API без ключа)."""
    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin,ethereum,the-open-network,solana"
        "&vs_currencies=usd&include_24hr_change=true"
    )
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                logging.warning(f"Crypto API error: {response.status}")
    except Exception as e:
        logging.error(f"Crypto fetch error: {e}")
    return None


def format_crypto_message(data) -> str:
    """Форматирует JSON от CoinGecko в красивое сообщение."""
    if not data:
        return "🚨 Не удалось получить данные о криптовалютах."

    lines = [
        f"<b>🪙 Крипто-сводка на {datetime.now().strftime('%d.%m')}</b>\n"
    ]
    coins = {
        "bitcoin": ("BTC", "Bitcoin"),
        "ethereum": ("ETH", "Ethereum"),
        "the-open-network": ("TON", "Toncoin"),
        "solana": ("SOL", "Solana")
    }

    for coin_id, (symbol, name) in coins.items():
        coin_data = data.get(coin_id)
        if not coin_data:
            continue

        price = coin_data.get("usd", 0)
        change = coin_data.get("usd_24h_change", 0)
        trend = "📈" if change > 0 else "📉"
        lines.append(
            f"• {name} ({symbol}): <b>${price:,.2f}</b> "
            f"{trend} <i>({change:+.2f}%)</i>"
        )

    lines.append("\n<i>Данные предоставлены CoinGecko</i>")
    return "\n".join(lines)


async def get_crypto_rates() -> str:
    """Основная функция для вызова извне."""
    data = await fetch_crypto_data()
    return format_crypto_message(data)
