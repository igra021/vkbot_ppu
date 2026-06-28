# bot_create.py
# Создаёт бота

from vkbottle.api import API
from vkbottle import Bot
from vkbottle.http import AiohttpClient
from config import state_dispenser, labeler
import aiohttp
from config import proxy, vk_token


def create_bot():
    """Фабричная функция для создания бота (вызывается внутри event loop)"""
     
    # Создаём connector с отключением SSL-проверки для Windows
    connector = aiohttp.TCPConnector(ssl=False)
    
    if proxy:
        # Создаём HTTP-клиент с прокси
        http_client = AiohttpClient(connector=connector, proxy=proxy)
    else:
        http_client = AiohttpClient(connector=connector)
    
    # Создаём API с HTTP-клиентом
    api = API(token=vk_token, http_client=http_client)
    
    # Создаём и возвращаем бота
    bot = Bot(
        api=api,
        labeler=labeler,
        state_dispenser=state_dispenser,
    )
    
    return bot

# bot = create_bot()