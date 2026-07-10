# llm\chat_gpt.py
# обработка ответов LLM, Rag
# получение истории их БД, сохранение сообщений в БД


from loguru import logger
import json
from .prompts import system_prompt, consultant_prompt
from db.database import save_message, get_history
from func_gpt import get_answer_llm

rag = None


# вызов из chat.py
async def chat_gpt(user_id: int, user_message: str, verbose: bool = False) -> str:
    """
    Обрабатывает сообщение пользователя с учётом истории из БД
    
    Args:
        user_id: ID пользователя ВКонтакте
        user_message: Текст сообщения
        verbose: Режим отладки
    
    Returns:
        str: Ответ бота
    """

    # 1. Сохраняем сообщение пользователя в БД
    await save_message(user_id, "user", user_message)
    
    # 2. Загружаем историю из БД (последние 20 сообщений)
    history = await get_history(user_id, limit=30)
    
    # 3. Формируем messages для LLM
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)  # Добавляем историю из БД
    
    # 4. Получаем ответ от LLM
    answer = await get_answer_llm(messages)
    
    if verbose:
        print('✅ Ответ ЛЛМ: ', answer)
    
    # 5. Парсим JSON
    try:
        data = json.loads(answer)
    except json.JSONDecodeError:
        logger.error(f"LLM вернул не JSON: {answer}")
        return "Произошла ошибка при обработке ответа. Повторите ваш вопрос"

    # парсинг ответа
    try:
        agent_command = data["Агент-аналитик"]['Имя агента']
        agent_message = data[agent_command]['Сообщение']

    # ошибка имени агента в отчете агента-аналитика
    except KeyError as e:
        logger.error(f"❌ Ошибка в имени агента в промте: {e}")
        return "Произошла ошибка при обработке ответа. Повторите ваш вопрос"   

    
    # 6. Если агент-консультант — пробуем RAG
    if agent_command == 'Агент-консультант':
        try: 
            data_consultant = data['Агент-консультант']
            data_query = data_consultant.get('Поисковый_запрос_RAG')
        except KeyError as e:
            logger.error(f"❌ Ошибка формирования Поискового запроса RAG в промте: {e}")
            return "Произошла ошибка при обработке ответа. Повторите ваш вопрос"

        try:    
            if data_query and rag:
                rag_answer = rag.search(data_query)

                if rag_answer and rag_answer != "not_found":
                    
                    # Формируем новый запрос с RAG без system
                    history_without_system = history  
                    rag_messages = [
                        {"role": "system", "content": consultant_prompt + " " + rag_answer}
                    ]
                    rag_messages.extend(history_without_system)
                    
                    # Получаем ответ с учётом RAG
                    rag_response = await get_answer_llm(rag_messages)
                    
                    if verbose:
                        print("\n📚 Ответ RAG:", rag_response, '\n')
                    
                    try:
                        rag_data = json.loads(rag_response)
                        final_answer = rag_data.get('answer', agent_message)
                    except json.JSONDecodeError:
                        logger.error(f"LLM консультант вернул не JSON: {answer}")
                        return "Произошла ошибка при обработке ответа. Повторите ваш вопрос"
                    
                    # Сохраняем ответ ассистента в БД
                    await save_message(user_id, "assistant", final_answer)
                    return final_answer
                else:
                    logger.error(f"RAG не нашел ответ на вопрос: {data_query}")
                    return "Не смог найти ответ на ваш вопрос"
        except Exception as e:
            logger.error(f"❌ Ошибка в chat_gpt: {e}")
            return "Произошла ошибка при обработке ответа. Повторите ваш вопрос"

        # 7. Сохраняем ответ ассистента в БД
        await save_message(user_id, "assistant", agent_message)
        return agent_message
