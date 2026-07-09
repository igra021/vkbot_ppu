# db\database.py
# функции работы с БД


import aiosqlite
from typing import List, Dict
from loguru import logger
import os

DB_PATH = "db\conversations.db"

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


async def save_message(user_id: int, role: str, content: str):
    """Сохраняет одно сообщение в БД (асинхронно)"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO conversations (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content)
        )
        await db.commit()


async def get_history(user_id: int, limit: int = 20) -> List[Dict[str, str]]:
    """Возвращает историю диалога пользователя (асинхронно)"""
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
