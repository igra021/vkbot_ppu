# llm/chat_gpt.py
# обработка ответов LLM, Rag
# получение истории из БД, сохранение сообщений в БД

import json
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
            answer_json = await get_answer_llm(messages)
            answer = json.loads(answer_json)
            
            # 7. Извлекаем вопрос и ответ
            agent_message = answer.get('Ответ_клиенту', '')
            search_query = answer.get('Вопрос_клиента', '')
            
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
       

        # 8. РАБОТА С RAG (если есть search_query и rag доступен)
        if search_query and rag:

            # Ищем ответ в RAG
            rag_answer = rag.search(search_query)
            
            if rag_answer:
                
                # Получаем ответ от LLM на основе ответа из RAG
                # формирую новую историю только для ЛЛМ + RAG:
                # из истории диалога убираем исходный системный промт и последний ответ ЛЛМ, оставляем только последний вопрос.
                # к системному промту добавляем "На основе информации из базы знаний сформируй ответ клиенту.\n\n" f"Информация из базы знаний:\n{rag_answer}\n\n"
                # передаю новую историю в ЛЛМ
                # получаю ответ, 
                #
                #
                try:
                    answer_json = await get_answer_llm(rag_messages)
        
                except Exception as e:
                    logger.error(f"❌ Ошибка получения ответа LLM с RAG: {e}")
                
                # Парсим ответ с RAG
                try:
                    answer = json.loads(answer_json)
                    agent_message = answer.get('Ответ_клиенту', '')
                
                except json.JSONDecodeError:
                    logger.error(f"❌ LLM с RAG вернул не JSON: {answer_json}")

        
        # 9. Добавляем полный ответ ассистента в сессию
        if agent_message and agent_message.strip():
            session_user.add_message("assistant", answer_json)
        else:
            logger.warning(f"⚠️ Пустой ответ для user_id={user_id}")
            agent_message = "Извините, я не могу ответить на ваш вопрос. Попробуйте переформулировать."
            session_user.add_message("assistant", agent_message)
        
        # 10. Сохраняем в БД (только если сессия "грязная")
        if session_user.is_dirty:
            
            # Сохраняем сообщение пользователя
            await save_message_to_db(user_id, "user", user_message)
            
            # Сохраняем полный ответ ассистента
            await save_message_to_db(user_id, "assistant", answer_json)

            # Сбрасываем флаг
            session_user.is_dirty = False  
            logger.debug(f"💾 Данные сохранены в БД для user_id={user_id}")
        
        return agent_message
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в chat_gpt: {e}")
        logger.exception("Полный стек ошибки:")
        return "Извините, произошла техническая ошибка. Попробуйте позже."