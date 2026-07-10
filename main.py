# main.py
# Запуск бота

import asyncio
import sys
import signal
from loguru import logger
from vkbottle import VKAPIError
from config import labeler, rag_file
from handlers.admin import admin_labeler
from handlers.chat import chat_labeler
from create_bot import create_bot
from llm.rag import RAGSystem
from db.database import init_db



def signal_handler(signum, frame):
    """Обработчик сигналов"""
    logger.info(f"🛑 Получен сигнал остановки {signum} в точке {frame}")
    # close_db()
    exit(0)

async def main():

    # Регистрируем обработчик сигнала
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Завершение от системы
    
    # Логирование - Отключаем DEBUG-уровень
    logger.remove()
    logger.add(sys.stderr, level="INFO")

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
    import llm.chat_gpt
    llm.chat_gpt.rag = rag

    # админовские команды
    labeler.load(admin_labeler) 
 
    # загружаю лабелер (группу хендлеров)
    labeler.load(chat_labeler)

    # создаю и запускаю бота
    bot = create_bot()
    try:
        logger.info("🤖 Бот запущен")
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

