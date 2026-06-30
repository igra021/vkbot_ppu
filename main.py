# main.py
# Запуск бота

import asyncio
import sys
import signal
from loguru import logger
from vkbottle import VKAPIError
from config import labeler, rag_file
from handlers import chat_labeler
from create_bot import create_bot
from llm.rag import RAGSystem



def signal_handler(signum, frame):
    """Обработчик сигналов"""
    logger.info(f"🛑 Получен сигнал остановки {signum} в точке {frame}")
    # Здесь можно добавить закрытие БД
    # db.close()
    exit(0)

async def main():

    # Регистрируем обработчик сигнала
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Завершение от системы
    
    # Логирование - Отключаем DEBUG-уровень
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    # загружаю RAG
    try:
        rag = RAGSystem(rag_file)
        logger.info('RAG загружен')
    except Exception as e:
        logger.error(f'Ошибка создания RAG {e}')

    # внедряю RAG в ЛЛМ через атрибут rag
    import llm.chat_gpt
    llm.chat_gpt.rag = rag
    
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
        # Например: db.close()
        logger.info("✅ Бот успешно остановлен")


# Стандартный запуск
if __name__ == "__main__":
    asyncio.run(main())

