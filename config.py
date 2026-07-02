# config.py
# читает параметры настройки


import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from vkbottle import BuiltinStateDispenser
from vkbottle.bot import BotLabeler

load_dotenv()

labeler = BotLabeler()
#state_dispenser = BuiltinStateDispenser()

# параметры из .env
api_key = os.getenv('OPENAI_API_KEY')
open_ai_model = os.getenv('OPENAI_MODEL')
base_url = os.getenv('OPENAI_URL')
temperature = float(os.getenv('OPENAI_TEMPERATURE'))
client = AsyncOpenAI(api_key=api_key, base_url=base_url,)
embeddings_model=os.getenv('Embeddings_model')

rag_file = os.getenv('rag_file')

vk_token = os.getenv('VK_token')
proxy = os.getenv('proxy')
vk_admin = int(os.getenv('vk_admin'))
verbose = bool(os.getenv('verbose'))





