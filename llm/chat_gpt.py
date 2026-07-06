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

    # добавляем вопрос ЛЛМ в историю
    history.append({"role": "assistant", "content": answer})
    agent_message = ''

    if verbose:
        print('✅ Ответ ЛЛМ: ', answer)
        # print('📌 ', history)

    try:
        data = json.loads(answer)

        """
        {"Агент-аналитик": 
  {
    "Потребности клиента": [],
    "Возражения клиента": [],
    "Тип клиента": "",
    "Общий комментарий": "Клиент задал вопрос, не относящийся к теме утепления.",
    "Важные фразы клиента дословно": ["как сварить пельмени"],
    "Следующий шаг": "Вернуться к теме утепления и задать вопрос о потребностях клиента."
  },
  "Агент-выявления потребностей": {
    "Сообщение": "Это не относится к теме нашей беседы. Давайте вернёмся к утеплению вашего дома. Почему вы рассматриваете утепление? Что именно хотите утеплить?",
    "Тип_ответа_консультанта": "",
    "Поисковый_запрос_RAG":""
  }
}
        """
        # исправить код - надо найти ключ по имени агента, ниже не правильно
        agent_command = data["Агент-аналитик"]['Следующий шаг']
        
        if agent_command.startswith('Агент-выявления потребностей'):
            agent_message = data["Агент-выявления потребностей"]['Сообщение']

        if agent_command.startswith('Агент-консультант'):
            agent_message = data["Агент-консультант"]['Сообщение']

        if agent_command.startswith('Агент-презентатор'):
            agent_message = data["Агент-презентатор"]['Сообщение']            

        if agent_command.startswith('Агент-закрытия возражений'):
            agent_message = data["Агент-закрытия возражений"]['Сообщение']   

        if agent_command.startswith('Агент-тип клиента'):
            agent_message = data["Агент-тип клиента"]['Сообщение']  
        

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