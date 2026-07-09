# db\database.py
# функции работы с БД


import sqlite3
from typing import List, Dict
from loguru import logger
import os

DB_PATH = "conversations.db"

# Глобальное соединение (синглтон)
_connection = None


def get_connection():
    """
    Возвращает соединение с БД (синглтон).
    Создаёт новое, если его нет.
    """
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(DB_PATH)
        _connection.row_factory = sqlite3.Row
        logger.info(f"🔗 Соединение с БД создано: {DB_PATH}")
    return _connection


def init_db():
    """Создаёт таблицы для хранения диалогов"""
    os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON conversations(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp)")
        conn.commit()


def save_message(user_id: int, role: str, content: str):
    """Сохраняет одно сообщение в БД"""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO conversations (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content)
        )
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения сообщения: {e}")
        raise


def get_history(user_id: int, limit: int = 20) -> List[Dict[str, str]]:
    """
    Возвращает историю диалога пользователя (последние limit сообщений)
    в хронологическом порядке
    """
    conn = get_connection()
    cursor = conn.execute(
        "SELECT role, content FROM conversations WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit)
    )
    rows = cursor.fetchall()
    return [{"role": row[0], "content": row[1]} for row in rows[::-1]]


def clear_history(user_id: int):
    """Очищает историю диалога пользователя"""
    conn = get_connection()
    conn.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
    conn.commit()


def get_all_users() -> List[int]:
    """Возвращает список всех пользователей, у которых есть диалоги"""
    conn = get_connection()
    cursor = conn.execute("SELECT DISTINCT user_id FROM conversations")
    return [row[0] for row in cursor.fetchall()]


def get_statistics() -> Dict[str, int]:
    """Возвращает статистику по БД"""
    conn = get_connection()
    cursor = conn.execute("SELECT COUNT(*) FROM conversations")
    total_messages = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(DISTINCT user_id) FROM conversations")
    total_users = cursor.fetchone()[0]
    
    return {
        "total_messages": total_messages,
        "total_users": total_users
    }


def close_db():
    """Закрывает глобальное соединение с БД при остановке бота"""
    global _connection
    if _connection:
        try:
            _connection.close()
            logger.info("🔒 Соединение с БД закрыто")
        except Exception as e:
            logger.error(f"❌ Ошибка при закрытии БД: {e}")
        finally:
            _connection = None
    else:
        logger.info("ℹ️ Соединение с БД уже закрыто")