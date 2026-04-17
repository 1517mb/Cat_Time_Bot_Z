import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging():
    """
    Настраивает глобальное логирование проекта.
    Пишет логи в консоль и в ротируемые файлы (папка logs/).
    """
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_format = "%(asctime)s - [%(levelname)s] - (%(filename)s:%(lineno)d) - %(message)s"  # noqa
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, datefmt=date_format)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    file_handler = RotatingFileHandler(
        filename=os.path.join(log_dir, "cat_bot.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    logging.info("Система логирования успешно инициализирована.")
