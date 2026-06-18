# llm\chat_gpt.py
# обработка ответов

from config import client
from .prompts import system_prompt
from .rag import rag

async def chat_gpt(message):
    # поиск ответа в RAG
    #answer = rag()
    
    # формирование ответа на сообщение клиента
    result = message    

    return result
