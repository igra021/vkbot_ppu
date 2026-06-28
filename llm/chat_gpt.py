# llm\chat_gpt.py
# обработка ответов

from config import client, open_ai_model, temperature
# from bd.func_bd import get_history
from .prompts import system_prompt
# from .rag import rag

# история диалога
history = [{"role": "system", "content": system_prompt}]

async def chat_gpt(user_message, verbose=False):
    
    # добавляем в историю
    history.append({"role": "user", "content": user_message})

    # поиск ответа в RAG
    #answer = rag()
    
    # формирование ответа на сообщение клиента
    response = await client.chat.completions.create(
        model=open_ai_model,
        messages=history,
        temperature=temperature,
    )
    answer = response.choices[0].message.content
    result_split = answer.split('splitter')
    if len(result_split) > 1:
        result = result_split[-1].strip()
    else:
        result = result_split[0].strip()

    # добавляем в историю
    history.append({"role": "assistant", "content": answer})
    if verbose:
        print('💤 Клиент: ', user_message)
        print('✅ Ответ ЛЛМ: ', answer)
        #print('📌 ', history[1::])

    return result