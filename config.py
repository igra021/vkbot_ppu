# config.py
# читает параметры настройки

import asyncio
from vkbottle import Bot
from vkbottle.api import API
from vkbottle.http import AiohttpClient
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('token')
proxy = os.getenv('proxy')
vk_admin = os.getenv('vk_admin')

