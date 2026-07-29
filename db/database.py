# db/database.py
# функции работы с БД

import aiosqlite
import json
from typing import List, Dict, Optional
from loguru import logger
import os

DB_PATH = os.path.join("db", "database.db")


async def init_db():
    """Создаёт таблицы для хранения диалогов"""
    os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON conversations(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp)")
        await db.commit()
        logger.info("✅ База данных инициализирована")


async def save_message_to_db(
    user_id: int, 
    role: str, 
    content: str
):
    """
    Сохраняет одно сообщение в БД (асинхронно)
    
    Args:
        user_id: ID пользователя
        role: 'user' или 'assistant'
        content: Текст сообщения
    """
    # Проверяем, что сообщение не пустое
    if not content:
        logger.warning(f"⚠️ Попытка сохранить пустое сообщение для user_id={user_id}")
        content = "[пустое сообщение]"
    
   
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO conversations (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content)
        )
        await db.commit()
        logger.debug(f"💾 Сообщение сохранено: user_id={user_id}, role={role}")


async def get_history_from_db(
    user_id: int, 
    limit: int = 30
) -> List[Dict[str, str]]:
    """
    Возвращает историю диалога пользователя (асинхронно)
    Только role и content — для передачи в LLM
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT role, content FROM conversations WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            # Разворачиваем для правильного порядка (от старых к новым)
            history = [{"role": row[0], "content": row[1]} for row in rows[::-1]]
            return history


async def clear_history(user_id: int):
    """Очищает историю диалога пользователя (асинхронно)"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
        await db.commit()
        logger.info(f"🗑️ История пользователя {user_id} очищена")


async def get_all_users() -> List[int]:
    """Возвращает список всех пользователей, у которых есть диалоги"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT DISTINCT user_id FROM conversations") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def get_statistics() -> Dict[str, int]:
    """Возвращает статистику по БД"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Всего сообщений
        async with db.execute("SELECT COUNT(*) FROM conversations") as cursor:
            total_messages = (await cursor.fetchone())[0]
        
        # Всего пользователей
        async with db.execute("SELECT COUNT(DISTINCT user_id) FROM conversations") as cursor:
            total_users = (await cursor.fetchone())[0]
        
        return {
            "total_messages": total_messages,
            "total_users": total_users
        }