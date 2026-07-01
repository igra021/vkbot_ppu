# llm\chat_gpt.py
# обработка ответов LLM, Rag

from loguru import logger
import json
from config import client, open_ai_model, temperature, rag_file
# from bd.func_bd import get_history
from .prompts import system_prompt

rag = None

# история диалога
history = [{"role": "system", "content": system_prompt}]

async def chat_gpt(user_message, verbose=False):
    
    # добавляем в историю
    history.append({"role": "user", "content": user_message})
    
    # формирование ответа на сообщение клиента
    response = await client.chat.completions.create(
        model=open_ai_model,
        messages=history,
        temperature=temperature,
        response_format={"type": "json_object"} 
    )
    answer = response.choices[0].message.content

    # добавляем ответ ЛЛМ в историю
    history.append({"role": "assistant", "content": answer})

    if verbose:
        print('✅ Ответ ЛЛМ: ', answer)
        # print('📌 ', history)


    try:
        data = json.loads(answer)
        agent_message = data.get("Сообщение агента", answer)
        
        object_type = data.get("Конструктивная часть", "")
        agent = data.get("Агент", "")
        if verbose:
            logger.info(f"Агент: {agent}")

        """
        if agent == 'Агент-консультант' and rag:
            # ищем ответ в раг
            rag_answer = 'Ответ РАГ: ' + rag.search(user_message, object_type)
            return rag_answer
        
        else:    
        """
        return agent_message

                    
    except json.JSONDecodeError:
        # Если ответ не в JSON, возвращаем как есть
        logger.warning(f"LLM вернул не JSON: {answer}")
        return "LLM вернул не JSON:" + answer