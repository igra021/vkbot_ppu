# llm\chat_gpt.py
# обработка ответов LLM, Rag
# получение истории их БД, сохранение сообщений в БД

import json
from loguru import logger
from .prompts_v2 import system_prompt
from db.database import save_message_to_db, get_history_from_db
from .func_gpt import get_answer_llm
from session_manager import session_manager
from .parsing_answer import parsing_answer
from config import DEBUG


rag = None


# вызов из chat.py
@logger.catch
async def chat_gpt(user_id: int, user_message: str) -> str:
    """
    Обрабатывает сообщение пользователя с учётом истории из БД
    
    Args:
        user_id: ID пользователя ВКонтакте
        user_message: Текст сообщения
    
    Returns:
        str: Ответ бота
    """
    try:
        # 1. Получаем сессию пользователя
        session_user = session_manager.get_session(user_id)
        
        # 2. Если сессия новая или истекла, загружаем историю из БД
        if not session_user.history:
            history_from_db = await get_history_from_db(user_id, limit=30)
            if history_from_db:
                session_user.history = history_from_db
                logger.debug(f"📚 Загружено {len(history_from_db)} сообщений из БД для {user_id}")

        # 3. Добавляем новое сообщение в историю
        session_user.add_message("user", user_message)
        
        # 4. Формируем историю диалога (история уже в сессии)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(session_user.history)
        
        # 5. Получаем ответ от LLM
        try:
            answer_json = await get_answer_llm(messages)
            answer = json.loads(answer_json)
        except Exception as e:
            logger.error(e)
            return "Произошла ошибка в работе ЛЛМ. Повторите ваш вопрос"
        except json.JSONDecodeError:
            logger.error(f"LLM вернул не JSON: {answer_json}")
            return "Ошибка в структуре ответа. Повторите ваш вопрос"     

        # парсинг ответа
        analitika, agent_message = await parsing_answer(answer, session_user.history)
            
        # 7. Добавляем ответ в историю
        session_user.add_message("assistant", agent_message)
        
        # 8. Сохраняем в БД распарсенный ответ агента и пользователя
        await save_message_to_db(user_id, "user", user_message)
        await save_message_to_db(user_id, "assistant", analitika)
        
        return agent_message
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return "Извините, произошла ошибка."    

    

    
    
