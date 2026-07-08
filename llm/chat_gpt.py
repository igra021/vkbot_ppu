# llm\chat_gpt.py
# обработка ответов LLM, Rag

from loguru import logger
import json
from config import client, open_ai_model, temperature
# from bd.func_bd import get_history
from .prompts import system_prompt, consultant_prompt

rag = None

# история диалога
history = [{"role": "system", "content": system_prompt}]

# LLM
async def get_answer_llm(history):
    response = await client.chat.completions.create(
        model=open_ai_model,
        messages=history,
        temperature=temperature,
        response_format={"type": "json_object"} 
    )
    return response.choices[0].message.content


async def chat_gpt(user_message, verbose=False):
    
    # добавляем в историю
    history.append({"role": "user", "content": user_message})
    
    # формирование ответа на сообщение клиента
    answer = await get_answer_llm(history)

    agent_message = ''

    if verbose:
        print('✅ Ответ ЛЛМ: ', answer)
        # print('📌 ', history)

    try:
        data = json.loads(answer)
        rag_answer = None
        data_query = None

        # исправить код - надо найти ключ по имени агента, ниже не правильно
        agent_command = data["Агент-аналитик"]['Имя агента']
        agent_message = data[agent_command]['Сообщение']

        if agent_command == 'Агент-консультант':
            data_consultant = data['Агент-консультант']
            data_query = data_consultant.get('Поисковый_запрос_RAG')
            if data_query:
                rag_answer = rag.search(data_query)
            else:
                return agent_message
            
            if rag_answer:
                # обработка ответа из РАГ. Системный промт консультанта
                history2 = [{"role": "system", "content": consultant_prompt + " " + rag_answer}]
                history2.extend(history[1:])   
                
                # print("\n", history2, '\n')                         

                response = await get_answer_llm(history2)
                
                print("\n", response, '\n') 

                data = json.loads(response)
                answer = data['answer']
                # добавляем сообщение ЛЛМ в историю
                history.append({"role": "assistant", "content": answer})    
                return answer

        # добавляем сообщение ЛЛМ в историю
        history.append({"role": "assistant", "content": answer})    

        return agent_message
                    
    except json.JSONDecodeError:
        # Если ответ не в JSON, возвращаем как есть
        logger.warning(f"LLM вернул не JSON: {answer}")
        return "LLM вернул не JSON:" + answer