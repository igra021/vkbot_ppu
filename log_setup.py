# logging.py

import os
from loguru import logger
from datetime import datetime


# Логирование
def log_setup():
    today = datetime.now().strftime('%Y-%m-%d')
    log_path = os.path.join('log', f'log_{today}.log')
    logger.remove()
    custom_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | " # <level> отвечает за цвет уровня
    "<cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>" # и здесь тоже
    )
    logger.add(log_path, enqueue=True, level='INFO', format=custom_format, rotation='00:00', retention='30 days', encoding="utf-8")