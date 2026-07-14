# main.py
# Запуск бота

import asyncio
import signal, os
from loguru import logger
from vkbottle import VKAPIError
from config import labeler, rag_file, DEBUG
from handlers.admin import admin_labeler
from handlers.chat import chat_labeler
from create_bot import create_bot
from llm.rag import RAGSystem
from db.database import init_db
from log_setup import log_setup


def signal_handler(signum, frame):
    """Обработчик сигналов"""
    logger.info(f"🛑 Получен сигнал остановки {signum} в точке {frame}")
    # close_db()
    exit(0)

async def main():

    # Регистрируем обработчик сигнала
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Завершение от системы
    
    # настройка логирования
    log_setup()

    # 1. ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
    try:
        await init_db()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        return  # Прерываем запуск, если БД не создалась

    # 1. Инициализируем RAG с проверкой
    try:
        rag = RAGSystem(rag_file)
        if rag.is_ready():
            logger.info("✅ RAG-система загружена и готова к работе")
        else:
            logger.warning("⚠️ RAG-система загружена, но база данных недоступна")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка загрузки RAG: {e}")
        rag = None

    # внедряю RAG в ЛЛМ через атрибут rag
    import llm.parsing_answer
    llm.parsing_answer.rag = rag

    # админовские команды
    labeler.load(admin_labeler) 
 
    # загружаю лабелер (группу хендлеров)
    labeler.load(chat_labeler)

    # создаю и запускаю бота
    bot = create_bot()
    try:
        logger.info("🤖 Бот запущен")
        if DEBUG:
            print(("🤖 Бот запущен"))

        await bot.run_polling()
    except KeyboardInterrupt:
        logger.info(f"❌ Ctrl+C Остановка пользователем") 
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")  
    except VKAPIError as e:
        logger.error(f"❌ Ошибка VKAPI: {e.code}")              
    finally:
        logger.info("🧹 Выполняем очистку перед выходом...")
        logger.info("✅ Бот успешно остановлен")


# Стандартный запуск
if __name__ == "__main__":
    asyncio.run(main())

