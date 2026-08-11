# llm/chat_gpt.py
# обработка ответов LLM, Rag
# получение истории из БД, сохранение сообщений в БД

from loguru import logger
from db.database import save_message_to_db, get_history_from_db
from session_manager import session_manager
from config import DEBUG, client, open_ai_model, temperature
import json, re, os
from llm.prompt import system_prompt


rag = None


def load_prompt(file_path: str, file_name: str) -> str:
    """Загружает промпт из XML файла"""

    with open(os.path.join(file_path, file_name), 'r', encoding='utf-8') as f:
        return f.read()


def save_to_file(text, messages):
    """Записывает поясняющий текст text и сообщения messages в файл messages.txt"""

    with open('messages.txt', 'a', encoding='utf-8') as f:
        f.write('---------\n')
        f.write(f'------ {text}\n')
        if type(messages) is str:
            f.write(messages)
            f.write('\n')
        else:    
            for el in messages:
                f.write(str(el))
                f.write('\n')


# -----------вызов из chat.py--------------

@logger.catch
async def chat_gpt(user_id: int, user_message: str) -> str:

    # ------ Подготовка полной сессии клиента с последним сообщением ---------
    # 1. Получаем сессию пользователя и историю из памяти
    session_user = session_manager.get_session(user_id)

    # 2. Если сессия новая (нет истории), загружаем из БД
    if not session_user.history:
        history_from_db = await get_history_from_db(user_id, limit=100)
        if history_from_db:
            session_user.history = history_from_db
            logger.debug(f"📚 Загружено {len(history_from_db)} сообщений из БД для {user_id}")
    
    # 3. Добавляем новое сообщение пользователя в сессию и в историю (через sesion manager)
    session_user.add_message("user", user_message)


    # ── TOOL DEFINITIONS ──────────────────────────────────────────────────────────
    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "search_rag",
                "description": "Поиск информации в базе знаний компании",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Поисковый запрос"}
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_cost",
                "description": "Рассчитать стоимость утепления на основе материала, объекта, площади",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "material": {"type": "string", "description": "Материал конструкции (по умолчанию 'дерево' для мансарды)"},
                        "object_type": {"type": "string", "description": "Тип объекта: стены, пол, мансарда, фундамент, потолок"},
                        "area": {"type": "integer", "description": "Площадь в кв.м."}
                    },
                    "required": ["material","object_type"]
                }
            }
        }
    ]

    # Загрузка промпта XML
    # system_prompt = load_prompt('llm', 'system_prompt.xml')

    # добавил системный промт к истории из сессии клиента
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    messages.extend(session_user.history)
     
    if rag:
        tool_dispatch = {
            "calculate_cost": rag.calculate_cost,
            "search_rag": rag.search_rag
            }
    else:
        tool_dispatch = {}

    # формируем ответ ЛЛМ
    try:
        while True:
            response = await client.chat.completions.create(
                model=open_ai_model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=temperature,
                response_format={"type": "json_object"}
            )

            message = response.choices[0].message
            # Добавляем полное сообщение ассистента в историю
            messages.append(message.model_dump())

            # Если нет вызовов инструментов — это финальный ответ
            if not message.tool_calls:
                logger.debug(f"✅ Ответ ЛЛМ: {message.content}")
                break

            # Обрабатываем каждый вызов
            for tool_call in message.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                fn = tool_dispatch.get(name)
                result = fn(**args) if fn else f"Unknown tool: {name}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),  # тоже приводим к строке
                })
            # Цикл повторится
        

        # 9. Добавляем ответ ассистента в сессию
        session_user.add_message("assistant", message.content)
        
        # 10. Сохраняем в БД (только если сессия "грязная")
        if session_user.is_dirty:
            
            # Сохраняем сообщение пользователя
            await save_message_to_db(user_id, "user", user_message)
            
            # Сохраняем ответ ассистента
            await save_message_to_db(user_id, "assistant", message.content)

            # Сбрасываем флаг
            session_user.is_dirty = False  
            logger.debug(f"💾 Данные сохранены в БД для user_id={user_id}")
        
        return message.content
            

    except Exception as e:
        logger.error(f"❌ Ошибка получения ответа от LLM: {e}")
        return "Произошла ошибка в работе LLM. Повторите ваш вопрос"         
       

        

        
        
        
