# llm\chat_gpt.py
# обработка ответов

from config import client, open_ai_model, temperature
from bd.func_bd import get_history
from .prompts import system_prompt
from .rag import rag

# история диалога
history = [{"role": "system", "content": system_prompt}]



async def chat_gpt(message):
    # поиск ответа в RAG
    #answer = rag()
    
    # история диалога
    """
    history = [
        {"role": "user", "content": "Здравствуйте! Меня интересует утепление стен."},
        {"role": "assistant", "content": "Здравствуйте! Мы используем для этого напыляемый пенополиуретан. Это эффективно и долговечно."},
        {"role": "user", "content": "А сколько это стоит за квадратный метр?"}
    ]
    """

    # формирование ответа на сообщение клиента
    response = client.chat.completions.create(
        model=open_ai_model,
        messages=history,
        temperature=temperature,
    )
    result = response.choices[0].message.content

    # добавляем в историю
    history.append

    return result