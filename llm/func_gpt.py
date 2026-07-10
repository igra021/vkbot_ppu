# llm/func_gpt.py
# функция вызова ЛЛМ, обработка ошибок

from loguru import logger
import json
import asyncio
from config import client, open_ai_model, temperature
from openai import APIError, APIConnectionError, RateLimitError, AuthenticationError, BadRequestError

async def get_answer_llm(messages, retry_count: int = 3, retry_delay: int = 2) -> str:
    """
    Отправляет запрос в LLM с обработкой ошибок и повторными попытками
    
    Args:
        messages: Список сообщений для отправки
        retry_count: Количество попыток при ошибке
        retry_delay: Задержка между попытками (секунды)
    
    Returns:
        str: Ответ от LLM или сообщение об ошибке
    
    Raises:
        Exception: Если все попытки не удались
    """
    
    for attempt in range(retry_count):
        try:
            logger.info(f"🔄 Попытка {attempt + 1}/{retry_count} запроса к LLM")
            
            response = await client.chat.completions.create(
                model=open_ai_model,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"},
                timeout=60.0  # Таймаут 60 секунд
            )
            
            # Проверяем, что ответ содержит данные
            if not response or not response.choices:
                raise ValueError("Пустой ответ от LLM")
            
            content = response.choices[0].message.content
            
            if not content or not content.strip():
                raise ValueError("Пустое содержимое ответа")
            
            return content
            
        except AuthenticationError as e:
            logger.error(f"❌ Ошибка аутентификации OpenAI: {e}")
            raise Exception("Неверный API-ключ OpenAI. Проверьте .env файл.")
            
        except RateLimitError as e:
            logger.warning(f"⚠️ Превышен лимит запросов: {e}")
            if attempt < retry_count - 1:
                wait_time = retry_delay * (attempt + 1)  # Экспоненциальная задержка
                logger.info(f"⏳ Ожидание {wait_time} секунд перед повторной попыткой...")
                await asyncio.sleep(wait_time)
                continue
            else:
                raise Exception("Превышен лимит запросов к OpenAI. Попробуйте позже.")
                
        except APIConnectionError as e:
            logger.warning(f"⚠️ Ошибка соединения с OpenAI: {e}")
            if attempt < retry_count - 1:
                await asyncio.sleep(retry_delay)
                continue
            else:
                raise Exception("Не удалось подключиться к OpenAI. Проверьте интернет-соединение.")
                
        except APIError as e:
            logger.error(f"❌ Ошибка API OpenAI: {e}")
            if attempt < retry_count - 1:
                await asyncio.sleep(retry_delay)
                continue
            else:
                raise Exception(f"Ошибка OpenAI: {str(e)}")
                
        except BadRequestError as e:
            logger.error(f"❌ Неверный запрос к OpenAI: {e}")
            # Это ошибка клиента (неправильный запрос) — повторять бесполезно
            raise Exception(f"Неверный запрос к OpenAI: {str(e)}")
            
        except asyncio.TimeoutError:
            logger.warning(f"⚠️ Таймаут запроса к OpenAI")
            if attempt < retry_count - 1:
                await asyncio.sleep(retry_delay)
                continue
            else:
                raise Exception("Превышено время ожидания ответа от OpenAI.")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON: {e}")
            raise Exception("Неверный формат ответа от OpenAI.")
            
        except Exception as e:
            logger.error(f"❌ Неизвестная ошибка: {e}")
            if attempt < retry_count - 1:
                await asyncio.sleep(retry_delay)
                continue
            else:
                raise Exception(f"Неизвестная ошибка при запросе к OpenAI: {str(e)}")
    
    # Если все попытки не удались
    raise Exception(f"Не удалось получить ответ от OpenAI после {retry_count} попыток")