# llm\chat_gpt.py
# обработка ответов LLM, Rag
# получение истории их БД, сохранение сообщений в БД


from loguru import logger
import json
from config import client, open_ai_model, temperature
from .prompts import system_prompt, consultant_prompt
from db.database import save_message, get_history

rag = None

# Вместо этого мы загружаем историю из БД при каждом запросе

async def get_answer_llm(messages):
    """Отправляет запрос в LLM"""
    response = await client.chat.completions.create(
        model=open_ai_model,
        messages=messages,
        temperature=temperature,
        response_format={"type": "json_object"} 
    )
    return response.choices[0].message.content


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
    try:
        # 1. Сохраняем сообщение пользователя в БД
        await save_message(user_id, "user", user_message)
        
        # 2. Загружаем историю из БД (последние 20 сообщений)
        history = await get_history(user_id, limit=20)
        
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
            agent_command = data["Агент-аналитик"]['Имя агента']
            agent_message = data[agent_command]['Сообщение']
            
            # 6. Если агент-консультант — пробуем RAG
            if agent_command == 'Агент-консультант':
                data_consultant = data['Агент-консультант']
                data_query = data_consultant.get('Поисковый_запрос_RAG')
                
                if data_query and rag:
                    rag_answer = rag.search(data_query)
                    if rag_answer and rag_answer != "not_found":
                        # Формируем новый запрос с RAG
                        history_without_system = history  # уже без system
                        
                        rag_messages = [
                            {"role": "system", "content": consultant_prompt + " " + rag_answer}
                        ]
                        rag_messages.extend(history_without_system)
                        
                        # Получаем ответ с учётом RAG
                        rag_response = await get_answer_llm(rag_messages)
                        
                        if verbose:
                            print("\n📚 Ответ с RAG:", rag_response, '\n')
                        
                        try:
                            rag_data = json.loads(rag_response)
                            final_answer = rag_data.get('answer', agent_message)
                        except:
                            final_answer = rag_response
                        
                        # Сохраняем ответ ассистента в БД
                        await save_message(user_id, "assistant", final_answer)
                        return final_answer
            
            # 7. Сохраняем ответ ассистента в БД
            await save_message(user_id, "assistant", agent_message)
            return agent_message
                    
        except json.JSONDecodeError:
            logger.warning(f"LLM вернул не JSON: {answer}")
            fallback = "LLM вернул не JSON: " + answer
            await save_message(user_id, "assistant", fallback)
            return fallback
            
    except Exception as e:
        logger.error(f"❌ Ошибка в chat_gpt: {e}")
        error_msg = "Извините, произошла ошибка. Попробуйте позже."
        await save_message(user_id, "assistant", error_msg)
        return error_msg