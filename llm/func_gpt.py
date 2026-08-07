# llm/func_gpt.py
# функция вызова ЛЛМ, обработка ошибок
# 

from config import client, open_ai_model, temperature
import os, json, re
from dotenv import load_dotenv
from openai import OpenAI
from prompt import system_prompt
from llm.rag import RAGSystem

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')     
base_url = 'https://api.proxyapi.ru/openai/v1'
client = OpenAI(api_key=api_key, base_url=base_url)


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
            "description": "Рассчитать стоимость утепления на основе площади, материала и объекта",
            "parameters": {
                "type": "object",
                "properties": {
                    "area": {"type": "integer", "description": "Площадь в кв.м."},
                    "material": {"type": "string", "description": "Материал конструкции (по умолчанию 'дерево' для мансарды)"},
                    "object_type": {"type": "string", "description": "Тип объекта: стены, пол, мансарда, фундамент, потолок"}
                },
                "required": ["area"]
            }
        }
    }
]


# Maps tool name → Python function for dynamic dispatch in the loop below


history = [
    {"role": "system", "content": system_prompt}
]

# ── AGENT LOOP ────────────────────────────────────────────────────────────────
def run_agent(messages: list) -> str:
    """
    Args: history
    """
    tool_dispatch = {"calculate_cost": RAGSystem.calculate_cost, "search_rag": RAGSystem.search_rag}

    while True:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        message = response.choices[0].message
        # Добавляем полное сообщение ассистента в историю
        messages.append(message.model_dump())

        # Если нет вызовов инструментов — это финальный ответ
        if not message.tool_calls:
            return message.content

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
        


# Запуск

while True:
    query = input("Клиент: ")
    history.append({"role": "user", "content": query})
    agent_message = run_agent(history)
    print("ЛЛМ: ", agent_message)