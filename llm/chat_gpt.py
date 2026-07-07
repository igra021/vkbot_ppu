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

        # исправить код - надо найти ключ по имени агента, ниже не правильно
        agent_command = data["Агент-аналитик"]['Следующий шаг']
        
        if agent_command.startswith('Агент-выявления потребностей'):
            agent_message = data["Агент-выявления потребностей"]['Сообщение']

        if agent_command.startswith('Агент-консультант'):
            agent_message = data["Агент-консультант"]['Сообщение']
            rag_answer = rag.search(data['Агент-консультант']['Поисковый_запрос_RAG'])
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

        if agent_command.startswith('Агент-презентатор'):
            agent_message = data["Агент-презентатор"]['Сообщение']            

        if agent_command.startswith('Агент-закрытия возражений'):
            agent_message = data["Агент-закрытия возражений"]['Сообщение']   

        if agent_command.startswith('Агент-тип клиента'):
            agent_message = data["Агент-тип клиента"]['Сообщение']  

        # добавляем сообщение ЛЛМ в историю
        history.append({"role": "assistant", "content": answer})    

        return agent_message
                    
    except json.JSONDecodeError:
        # Если ответ не в JSON, возвращаем как есть
        logger.warning(f"LLM вернул не JSON: {answer}")
        return "LLM вернул не JSON:" + answer