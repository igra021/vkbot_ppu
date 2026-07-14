# llm/parsing_answer.py
# достает ответ агента из ответа ЛЛМ

import json
from loguru import logger
from config import DEBUG
from .prompts_v2 import consultant_prompt
from .func_gpt import get_answer_llm

# Глобальная переменная RAG (устанавливается из main)
rag = None


@logger.catch
async def parsing_answer(agent_answer: dict, history: list) -> tuple:
    """
    Достает ответ агента из ответа ЛЛМ. Обращается к RAG если есть search_query,
    повторно обращается к ЛЛМ для формирования ответа
    
    Args:
        agent_answer: Ответ ЛЛМ в виде словаря
        history: история диалога пользователя из сессии
    
    Returns:
        tuple: (analitika, agent_message) — аналитика и сообщение для клиента
    """

    if DEBUG:
        logger.debug(f"📥 Парсинг ответа: {json.dumps(agent_answer, ensure_ascii=False)[:500]}...")

    # 1. Извлекаем аналитику и сообщение
    try:
        analitika = agent_answer.get('Аналитика', {})
        agent_message = agent_answer.get('Ответ_клиенту', '')

        
        # ✅ Правильное получение search_query
        search_query = analitika.get('search_query', '')
        
        if DEBUG:
            logger.debug(f"✅ Аналитика после сообщения клиента: {json.dumps(analitika, ensure_ascii=False, indent=2)}")
            logger.debug(f"✅ Сообщение: {agent_message[:100]}...")
            if search_query:
                logger.debug(f"🔍 search_query: {search_query}")

    except Exception as e:
        logger.error(f"❌ Ошибка извлечения данных из ответа: {e}")
        return {}, "Произошла ошибка при обработке ответа. Повторите ваш вопрос"

    # 2. Проверка на пустое сообщение
    if not search_query and not agent_message:
        logger.warning("⚠️ Пустое сообщение от агента")
        return analitika, "Извините, я не могу ответить на ваш вопрос. Попробуйте переформулировать."

    # 3. ✅ РАБОТА С RAG (если есть search_query и rag доступен)
    if search_query and rag:
        logger.info(f"🔍 Поиск в RAG: {search_query}")
        
        try:
            # Ищем ответ в RAG
            rag_answer = rag.search(search_query)
            
            if rag_answer and rag_answer != "not_found":
                logger.debug(f"📚 Найден ответ RAG: {rag_answer[:100]}...")
                
                # Формируем новую историю с RAG
                rag_messages = [
                    {"role": "system", "content": consultant_prompt + " " + rag_answer}
                ]
                rag_messages.extend(history)
                logger.debug(f"История диалога для RAG: {rag_messages}")

                # Получаем ответ от LLM на основе RAG
                try:
                    rag_response = await get_answer_llm(rag_messages)
                    logger.debug(f"📚 Ответ LLM с RAG: {rag_response[:200]}...")
                except Exception as e:
                    logger.error(f"❌ Ошибка получения ответа LLM с RAG: {e}")
                    return analitika, agent_message  # Возвращаем обычный ответ
                
                # Парсим ответ с RAG
                try:
                    rag_data = json.loads(rag_response)
                    rag_message = rag_data.get('answer', rag_response)
                    return analitika, rag_message
                except json.JSONDecodeError:
                    logger.error(f"❌ LLM с RAG вернул не JSON: {rag_response}")
                    return analitika, agent_message  # Возвращаем обычный ответ
            
            else:
                logger.warning(f"⚠️ RAG не нашёл ответ: {search_query}")
                return analitika, agent_message  # Возвращаем обычный ответ
                
        except Exception as e:
            logger.error(f"❌ Ошибка RAG: {e}")
            return analitika, agent_message  # Возвращаем обычный ответ
    
    # 4. Возвращаем обычный ответ (без RAG)
    return analitika, agent_message