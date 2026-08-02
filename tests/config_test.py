# tests/config_test.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Клиент для тестов
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    base_url=os.getenv('OPENAI_URL', 'https://api.openai.com/v1')
)

# Модель для тестов (можно ту же, что и в боте)
MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')