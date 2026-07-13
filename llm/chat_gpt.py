# llm\chat_gpt.py
# обработка ответов LLM, Rag
# получение истории их БД, сохранение сообщений в БД


from loguru import logger
import json
from .prompts import system_prompt, consultant_prompt
from db.database import save_message, get_history
from .func_gpt import get_answer_llm
from session_manager import session_manager
from .parsing_answer import parsing_answer

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
    try:
        # 1. Получаем сессию пользователя
        session = session_manager.get_session(user_id)
        
        # 2. Если сессия новая или истекла, загружаем историю из БД
        if not session.history:
            history_from_db = await get_history(user_id, limit=30)
            if history_from_db:
                session.history = history_from_db
                logger.info(f"📚 Загружено {len(history_from_db)} сообщений из БД для {user_id}")

        # 3. Добавляем новое сообщение в сессию
        session.add_message("user", user_message)
        
        # 4. Формируем промпт (история уже в сессии)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(session.get_history(limit=30))
        
        # 5. Получаем ответ от LLM
        try:
            answer = await get_answer_llm(messages)
        except Exception as e:
            logger.error(e)
            return "Произошла ошибка в работе ЛЛМ. Повторите ваш вопрос"
    
        if verbose:
            print('✅ Ответ ЛЛМ: ', answer)


        # парсинг ответа
        agent_message = await parsing_answer()
        
            
            # 7. Добавляем ответ в сессию
            session.add_message("assistant", agent_message)
            
            # 8. Сохраняем в БД (можно асинхронно)
            await save_message(user_id, "user", user_message)
            await save_message(user_id, "assistant", agent_message)
            
            return agent_message
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return "Извините, произошла ошибка."    

    

    
    
