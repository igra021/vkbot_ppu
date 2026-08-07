# tests/test_prompt.py
import sys
import os

# Добавляем корневую папку проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import pytest
from loguru import logger
from config_test import client, MODEL
from llm.prompt import system_prompt


class TestPromptWithLLMClient:
    """Тестирование промта с LLM в роли клиента"""
    
    # Промт для LLM-клиента (играет роль пользователя)
    CLIENT_PROMPT = """
    Ты — клиент, который хочет утеплить свой дом пенополиуретаном (ППУ).
    Твоя задача — вести естественный диалог с консультантом по утеплению.
    
    ПРАВИЛА:
    1. Ты НЕ знаешь ничего о ППУ — ты обычный человек.
    2. Отвечай кратко, как в реальном чате (1-3 предложения).
    3. Иногда задавай вопросы:
       - о цене
       - о толщине утепления
       - о сроках
       - о качестве
    4. Иногда выражай сомнения (возражения):
       - "дорого"
       - "а это надёжно?"
       - "а выезд есть?"
    5. Не пиши длинные сообщения — ты обычный пользователь.
    6. Ты не знаешь, что такое ППУ — уточняй.
    
    Твой "персонаж":
    - У тебя дом из бруса, 100 кв.м.
    - Хочешь утеплить стены (можешь сказать это не сразу)
    - У тебя средний бюджет
    - Ты слышал про ППУ, но не уверен, что это лучше минваты
    
    Начни диалог с приветствия. Не пиши сразу всю информацию — выдавай постепенно.
    """
    
    def _call_llm(self, messages, role="bot"):
        """Вызов LLM с обработкой ошибок"""
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.7,
                response_format={"type": "json_object"} if role == "bot" else None
            )
            content = response.choices[0].message.content
            print(f"\n{'='*50}")
            print(f"🤖 Роль: {role}")
            print(f"📝 Ответ: {content}")
            print(f"{'='*50}\n")
            return content
        except Exception as e:
            logger.error(f"Ошибка вызова LLM: {e}")
            return None
    
    def _parse_bot_response(self, response):
        """Парсит JSON-ответ бота"""
        try:
            if isinstance(response, str):
                return json.loads(response)
            return response
        except json.JSONDecodeError:
            logger.error(f"Невалидный JSON: {response}")
            return {"Ответ_клиенту": response, "Вопрос_клиента": ""}
    
    def _run_dialog(self, max_turns: int = 10):
        """
        Запускает диалог между клиентом и ботом
        
        Args:
            max_turns: Максимальное количество обменов сообщениями
        
        Returns:
            list: История диалога
        """
        history = []
        
        # 1. Первое сообщение — клиент
        client_messages = [
            {"role": "system", "content": self.CLIENT_PROMPT},
            {"role": "user", "content": "Начни диалог с консультантом."}
        ]
        
        client_response = self._call_llm(client_messages, role="client")
        if not client_response:
            return []
        
        history.append({"role": "user", "content": client_response})
        print(f"\n👤 КЛИЕНТ: {client_response}")
        
        # 2. Цикл диалога
        for turn in range(max_turns):
            # 2.1. Бот отвечает
            bot_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": client_response}
            ]
            
            # Добавляем историю (для контекста)
            for msg in history[:-1]:
                bot_messages.append(msg)
            
            bot_response = self._call_llm(bot_messages, role="bot")
            if not bot_response:
                break
            
            bot_data = self._parse_bot_response(bot_response)
            bot_answer = bot_data.get("Ответ_клиенту", bot_response)
            
            history.append({"role": "assistant", "content": bot_answer})
            print(f"\n🤖 БОТ: {bot_answer}")
            
            # Проверяем, не предлагает ли бот оставить контакты
            if "номер" in bot_answer.lower() or "телефон" in bot_answer.lower():
                print("\n✅ БОТ ДОШЁЛ ДО КОНТАКТОВ!")
                break
            
            # 2.2. Клиент отвечает
            client_history = [
                {"role": "system", "content": self.CLIENT_PROMPT},
                {"role": "user", "content": f"Вот ответ консультанта: {bot_answer}\n\nТы клиент. Ответь на это сообщение."}
            ]
            
            # Добавляем историю для клиента
            for msg in history:
                client_history.append({"role": msg["role"], "content": msg["content"]})
            
            client_response = self._call_llm(client_history, role="client")
            if not client_response:
                break
            
            history.append({"role": "user", "content": client_response})
            print(f"\n👤 КЛИЕНТ: {client_response}")
            
            # Если клиент сказал "до свидания" или прощается
            if any(word in client_response.lower() for word in ["пока", "до свидания", "спасибо"]):
                print("\n🔚 КЛИЕНТ ЗАВЕРШИЛ ДИАЛОГ")
                break
        
        return history
    
    # ==================== ТЕСТЫ ====================
    
    def test_full_dialog(self):
        """Тест: полный диалог до получения контактов"""
        print("\n" + "="*60)
        print("🧪 НАЧАЛО ТЕСТА: ПОЛНЫЙ ДИАЛОГ")
        print("="*60)
        
        history = self._run_dialog(max_turns=15)
        
        # Проверяем, что диалог состоялся
        assert len(history) > 0, "Диалог не состоялся"
        
        # Проверяем, что были сообщения от обоих сторон
        roles = set(msg["role"] for msg in history)
        assert "user" in roles, "Нет сообщений от клиента"
        assert "assistant" in roles, "Нет сообщений от бота"
        
        # Проверяем, что бот использовал промт корректно
        assistant_messages = [msg["content"] for msg in history if msg["role"] == "assistant"]
        assert len(assistant_messages) > 0, "Бот не отвечал"
        
        print("\n" + "="*60)
        print("✅ ТЕСТ ПРОЙДЕН")
        print(f"📊 Всего сообщений: {len(history)}")
        print(f"🤖 Ответов бота: {len(assistant_messages)}")
        print("="*60)
    
    def test_bot_asks_questions(self):
        """Тест: бот должен задавать вопросы клиенту"""
        print("\n" + "="*60)
        print("🧪 ТЕСТ: БОТ ЗАДАЁТ ВОПРОСЫ")
        print("="*60)
        
        history = self._run_dialog(max_turns=5)
        
        # Проверяем, что бот задал хотя бы один вопрос
        assistant_messages = [msg["content"] for msg in history if msg["role"] == "assistant"]
        has_question = any("?" in msg for msg in assistant_messages)
        
        assert has_question, "Бот не задал ни одного вопроса"
        print(f"✅ Вопросы найдены")
    
    def test_bot_handles_price_question(self):
        """Тест: бот должен отвечать на вопрос о цене"""
        print("\n" + "="*60)
        print("🧪 ТЕСТ: ВОПРОС О ЦЕНЕ")
        print("="*60)
        
        # Формируем вопрос о цене
        client_messages = [
            {"role": "system", "content": self.CLIENT_PROMPT},
            {"role": "user", "content": "Задай вопрос о цене утепления."}
        ]
        
        price_question = self._call_llm(client_messages, role="client")
        print(f"👤 КЛИЕНТ: {price_question}")
        
        # Бот отвечает
        bot_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": price_question}
        ]
        
        bot_response = self._call_llm(bot_messages, role="bot")
        bot_data = self._parse_bot_response(bot_response)
        bot_answer = bot_data.get("Ответ_клиенту", bot_response)
        
        print(f"🤖 БОТ: {bot_answer}")
        
        # Проверяем, что бот ответил на вопрос
        assert bot_answer is not None, "Бот не ответил"
        assert len(bot_answer) > 10, "Ответ слишком короткий"
        
        # Проверяем, что бот не проигнорировал вопрос
        assert "цена" in bot_answer.lower() or "стоит" in bot_answer.lower(), "Бот не ответил на вопрос о цене"
    
    def test_bot_handles_objection(self):
        """Тест: бот должен обрабатывать возражения"""
        print("\n" + "="*60)
        print("🧪 ТЕСТ: ОБРАБОТКА ВОЗРАЖЕНИЙ")
        print("="*60)
        
        # Возражение от клиента
        client_message = "Дорого! Не хочу платить столько."
        
        bot_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": client_message}
        ]
        
        bot_response = self._call_llm(bot_messages, role="bot")
        bot_data = self._parse_bot_response(bot_response)
        bot_answer = bot_data.get("Ответ_клиенту", bot_response)
        
        print(f"🤖 БОТ: {bot_answer}")
        
        # Проверяем, что бот не игнорирует возражение
        assert bot_answer is not None, "Бот не ответил на возражение"
        
        # Проверяем, что бот не просто повторяет цену
        # (должен быть контраргумент или предложение)
        has_response = any(word in bot_answer.lower() for word in ["окупаемость", "экономия", "выгода", "надёжность"])
        # Или должен быть вопрос
        has_question = "?" in bot_answer
        
        assert has_response or has_question, "Бот не обработал возражение должным образом"
    
    def test_bot_generates_valid_json(self):
        """Тест: бот всегда возвращает валидный JSON"""
        print("\n" + "="*60)
        print("🧪 ТЕСТ: ВАЛИДНОСТЬ JSON")
        print("="*60)
        
        test_messages = [
            "привет",
            "сколько стоит утепление?",
            "хочу утеплить дом из бруса",
            "дорого",
            "пока"
        ]
        
        for msg in test_messages:
            bot_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": msg}
            ]
            
            bot_response = self._call_llm(bot_messages, role="bot")
            
            try:
                data = json.loads(bot_response)
                assert "Ответ_клиенту" in data, f"Нет поля 'Ответ_клиенту' для: {msg}"
                assert "Отчет" in data, f"Нет поля 'Отчет' для: {msg}"
                print(f"✅ JSON валидный для: {msg}")
            except json.JSONDecodeError:
                assert False, f"Невалидный JSON для: {msg}\nОтвет: {bot_response}"
    
    def test_bot_follows_sales_funnel(self):
        """Тест: бот ведёт клиента по воронке продаж"""
        print("\n" + "="*60)
        print("🧪 ТЕСТ: ВОРОНКА ПРОДАЖ")
        print("="*60)
        
        history = self._run_dialog(max_turns=20)
        
        assistant_messages = [msg["content"] for msg in history if msg["role"] == "assistant"]
        
        # Проверяем этапы воронки
        checkpoints = {
            "приветствие": any("Здравствуйте" in msg or "привет" in msg.lower() for msg in assistant_messages),
            "выявление_потребностей": any("объект" in msg.lower() or "материал" in msg.lower() for msg in assistant_messages),
            "презентация": any("толщина" in msg.lower() or "плотность" in msg.lower() for msg in assistant_messages),
        }
        
        print("📊 Результаты:")
        for stage, passed in checkpoints.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {stage}: {passed}")
        
        # Проверяем, что хотя бы некоторые этапы пройдены
        passed_count = sum(checkpoints.values())
        assert passed_count >= 1, "Бот не прошёл ни одного этапа воронки"