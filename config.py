# config.py
# читает параметры настройки


import os
from openai import OpenAI
from dotenv import load_dotenv
from vkbottle import BuiltinStateDispenser
from vkbottle.bot import BotLabeler

load_dotenv()

labeler = BotLabeler()
state_dispenser = BuiltinStateDispenser()

# параметры из .env
api_key = os.getenv('OPENAI_API_KEY')
vk_token = os.getenv('VK_token')
proxy = os.getenv('proxy')
vk_admin = os.getenv('vk_admin')
base_url = os.getenv('OPENAI_URL')
client = OpenAI(api_key=api_key, base_url=base_url,)




