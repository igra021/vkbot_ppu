# llm\chat_gpt.py
# обработка ответов
import json
from config import client, open_ai_model, temperature
# from bd.func_bd import get_history
from .prompts import system_prompt
# from .rag import rag

# список агентов которым нужен РАГ
rag_agents = ['Агент-консультант','Агент-презентатор','Агент-закрытия возражений']

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
    )
    answer = response.choices[0].message.content

    # добавляем ответ ЛЛМ в историю
    history.append({"role": "assistant", "content": answer})
    if verbose:
        print('✅ Ответ ЛЛМ: ', answer)
        #print('📌 ', history[1::])

    try:
        data = json.loads(answer)
        agent_message = data.get("Сообщение агента", answer)
        agent = data.get("Агент", "")

        if agent in rag_agents:
            # ищем ответ в раг
            return agent_message
        else:    
            return agent_message
                    
    except json.JSONDecodeError:
        # Если ответ не в JSON, возвращаем как есть
        logger.warning(f"LLM вернул не JSON: {answer}")
        return answer