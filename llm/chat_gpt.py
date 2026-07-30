# llm/chat_gpt.py
# обработка ответов LLM, Rag
# получение истории из БД, сохранение сообщений в БД

from loguru import logger
from .prompts_v2 import system_prompt
from db.database import save_message_to_db, get_history_from_db
from .func_gpt import get_answer_llm
from session_manager import session_manager
from config import DEBUG
import pprint

rag = None


# вызов из chat.py
@logger.catch
async def chat_gpt(user_id: int, user_message: str) -> str:
    """
    Обрабатывает сообщение пользователя с учётом истории из БД.
    Использует сессии в памяти для снижения нагрузки на БД.
    
    Args:
        user_id: ID пользователя ВКонтакте
        user_message: Текст сообщения
    
    Returns:
        str: Ответ бота
    """
    try:
        # 1. Получаем сессию пользователя из памяти
        session_user = session_manager.get_session(user_id)
  
        # 2. Если сессия новая (нет истории), загружаем из БД
        if not session_user.history:
            history_from_db = await get_history_from_db(user_id, limit=30)
            if history_from_db:
                session_user.history = history_from_db
                logger.debug(f"📚 Загружено {len(history_from_db)} сообщений из БД для {user_id}")
        
               
        # 4. Формируем промт с аналитикой
        messages = [{"role": "system", "content": system_prompt}]
        
        # Добавляем историю из сессии (она уже в правильном порядке)
        messages.extend(session_user.history)
        
        # добавляю сообщение клиента
        messages.append({"role": "user", "content": user_message})
        
        # 5. Добавляем новое сообщение пользователя в сессию
        session_user.add_message("user", user_message)
        

        # 6. Получаем ответ от LLM
        try:
            answer_llm = await get_answer_llm(messages)
            
            # 7. Извлекаем вопрос и ответ
            agent_message = answer_llm.get('Ответ_клиенту', '')
            search_query = answer_llm.get('Вопрос_клиента', '')
            
            logger.debug(f"✅ Ответ ЛЛМ: {answer_llm}")
            print('\n--------answer----\n')
            pprint.pprint(answer_llm)
       
        except Exception as e:
            logger.error(f"❌ Ошибка получения ответа от LLM: {e}")
            return "Произошла ошибка в работе LLM. Повторите ваш вопрос"         
       

        # 8. РАБОТА С RAG (если есть search_query и rag доступен)
        if search_query and rag:

            # Ищем ответ в RAG
            rag_answer = rag.search(search_query)
            
            if rag_answer:

                # формирую новую историю только для ЛЛМ + RAG:
                # из истории диалога убираем исходный системный промт, оставляем только последний вопрос.
                rag_prompt = system_prompt + f"\nНа основе информации из базы знаний сформируй ответ клиенту. Информация из базы знаний:\n{rag_answer}"
                rag_messages = [{"role": "system", "content": rag_prompt}]
                rag_messages.extend(messages[1:])

                # Получаем ответ от LLM на основе ответа из RAG
                try:
                    answer_llm = await get_answer_llm(rag_messages)
                    agent_message = answer_llm.get('Ответ_клиенту', '')
                except Exception as e:
                    logger.error(f"❌ Ошибка получения ответа LLM с RAG: {e}")
                    return 'Ошибка получения ответа LLM с RAG'
        
        # 9. Добавляем ответ ассистента в сессию
        if agent_message and agent_message.strip():
            session_user.add_message("assistant", agent_message)
        else:
            logger.warning(f"⚠️ Пустой ответ для user_id={user_id}")
            agent_message = "Извините, я не могу ответить на ваш вопрос. Попробуйте переформулировать."
            session_user.add_message("assistant", agent_message)
        
        # 10. Сохраняем в БД (только если сессия "грязная")
        if session_user.is_dirty:
            
            # Сохраняем сообщение пользователя
            await save_message_to_db(user_id, "user", user_message)
            
            # Сохраняем ответ ассистента
            await save_message_to_db(user_id, "assistant", agent_message)

            # Сбрасываем флаг
            session_user.is_dirty = False  
            logger.debug(f"💾 Данные сохранены в БД для user_id={user_id}")
        
        return agent_message
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в chat_gpt: {e}")
        logger.exception("Полный стек ошибки:")
        return "Извините, произошла техническая ошибка. Попробуйте позже."