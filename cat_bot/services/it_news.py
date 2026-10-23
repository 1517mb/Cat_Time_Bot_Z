import asyncio
import logging
import xml.etree.ElementTree as ET

import aiohttp

logger = logging.getLogger(__name__)

HABR_RSS_URL = "https://habr.com/ru/rss/articles/all/?fl=ru"


async def fetch_it_news(count: int = 3) -> list[dict]:
    """Получает последние IT новости через RSS Habr."""
    news = []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(HABR_RSS_URL) as response:
                response.raise_for_status()
                xml_data = await response.text()
                root = ET.fromstring(xml_data)
                for item in root.findall("./channel/item")[:count]:
                    title = item.find("title").text
                    link = item.find("link").text
                    news.append({"title": title, "link": link})
    except aiohttp.ClientResponseError as error:
        logger.warning(
            "Habr RSS API returned HTTP %s", error.status,
            extra={"provider": "habr", "operation": "fetch_it_news"},
        )
    except (aiohttp.ClientError, asyncio.TimeoutError) as error:
        logger.warning(
            "Habr RSS request failed (%s): %s", type(error).__name__, error,
            extra={"provider": "habr", "operation": "fetch_it_news"},
        )
    except Exception:
        logger.exception(
            "Ошибка при получении новостей",
            extra={"provider": "habr", "operation": "fetch_it_news"},
        )
    return news
