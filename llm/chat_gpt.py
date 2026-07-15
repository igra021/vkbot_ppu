# llm/chat_gpt.py
# обработка ответов LLM, Rag
# получение истории из БД, сохранение сообщений в БД

import json
from loguru import logger
from .prompts_v2 import system_prompt
from db.database import save_message_to_db, get_history_from_db, get_last_analytics
from .func_gpt import get_answer_llm
from session_manager import session_manager
from .parsing_answer import parsing_answer
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
        
        # 3. Получаем предыдущую аналитику (если есть)
        previous_analytics = await get_last_analytics(user_id)
        if DEBUG and previous_analytics:
            logger.debug(f"📊 Предыдущая аналитика: {json.dumps(previous_analytics, ensure_ascii=False, indent=2)}")
            logger.debug(f"🆘 Сообщение клиента: {user_message}")
               
        # 4. Формируем промт с аналитикой
        messages = [{"role": "system", "content": system_prompt}]
        
        # Добавляем историю из сессии (она уже в правильном порядке)
        messages.extend(session_user.history)

        # Добавляем предыдущую аналитику как системный контекст (если есть)
        if previous_analytics:
            analytics_context = (
                "Предыдущая аналитика: \n"
                f"{json.dumps(previous_analytics, ensure_ascii=False, indent=2)}"
            )
            messages.append({"role": "assistant", "content": analytics_context})
        
        # добавляю сообщение клиента
        messages.append({"role": "user", "content": user_message})
        

        # 5. Добавляем новое сообщение пользователя в сессию
        session_user.add_message("user", user_message)
        
        print("--------сообщение клиента: ", user_message)

        # 6. Получаем ответ от LLM
        try:
            answer_json = await get_answer_llm(messages)
            answer = json.loads(answer_json)
            logger.debug(f"✅ Ответ ЛЛМ: {json.dumps(answer_json, ensure_ascii=False, indent=2)}")
            print('\n--------answer----\n')
            pprint.pprint(answer)

        except json.JSONDecodeError as e:
            logger.error(f"❌ LLM вернул не JSON: {answer_json}")
            logger.error(f"❌ Ошибка: {e}")
            return "Ошибка в структуре ответа. Повторите ваш вопрос"
        
        except Exception as e:
            logger.error(f"❌ Ошибка получения ответа от LLM: {e}")
            return "Произошла ошибка в работе LLM. Повторите ваш вопрос"         
       
        # 8. Парсинг ответа (получаем аналитику и сообщение для клиента)
        #    В parsing_answer уже обрабатывается RAG, если есть search_query
        try:
            analytics, agent_message = await parsing_answer(answer, session_user.history)
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга ответа: {e}")
            return "Произошла ошибка при обработке ответа. Повторите ваш вопрос"
        
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
            
            # Сохраняем ответ ассистента с аналитикой
            await save_message_to_db(user_id, "assistant", agent_message, analytics)
            session_user.is_dirty = False  # Сбрасываем флаг
            logger.debug(f"💾 Данные сохранены в БД для user_id={user_id}")
        
        return agent_message
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в chat_gpt: {e}")
        logger.exception("Полный стек ошибки:")
        return "Извините, произошла техническая ошибка. Попробуйте позже."