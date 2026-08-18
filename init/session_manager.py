# session_manager.py
from typing import Dict, List
from datetime import datetime, timedelta
from loguru import logger

class Session:
    """Сессия пользователя"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.history: List[Dict[str, str]] = []
        self.last_activity = datetime.now()
        self.is_dirty = False  # Нужно ли сохранять в БД
    
    def add_message(self, role: str, content: str):
        """Добавляет сообщение в историю"""
        self.history.append({"role": role, "content": content})
        self.is_dirty = True
        self.last_activity = datetime.now()
    
    def get_history(self, limit: int = 30) -> List[Dict[str, str]]:
        """Возвращает последние N сообщений"""
        return self.history[-limit:] if self.history else []
    
    def is_expired(self, timeout: int = 3600) -> bool:
        """Проверяет, истекла ли сессия (по умолчанию 1 час)"""
        return (datetime.now() - self.last_activity).seconds > timeout


class SessionManager:
    """Менеджер сессий"""
    
    def __init__(self, max_sessions: int = 1000, session_timeout: int = 3600):
        self.sessions: Dict[int, Session] = {}
        self.max_sessions = max_sessions
        self.session_timeout = session_timeout
    
    def get_session(self, user_id: int) -> Session:
        """Получает сессию пользователя"""

        # очистка старых сессий
        self._cleanup_expired()
        
        # создает новую сессию
        if user_id not in self.sessions:
            logger.debug(f"📝 Создана новая сессия для {user_id}")
            self.sessions[user_id] = Session(user_id)
        else:
            self.sessions[user_id].last_activity = datetime.now()
        
        return self.sessions[user_id]
    
    def _cleanup_expired(self):
        """Очищает истекшие сессии"""
        expired = [
            uid for uid, session in self.sessions.items()
            if session.is_expired(self.session_timeout)
        ]
        
        for uid in expired:
            del self.sessions[uid]
        
        if expired:
            logger.debug(f"🗑️ Удалено {len(expired)} истекших сессий")
    
    # вызов из хэндлера admin - очистка истории
    def clear_session(self, user_id: int):
        """Очищает сессию пользователя"""
        if user_id in self.sessions:
            del self.sessions[user_id]
            logger.info(f"🗑️ Сессия {user_id} очищена")

# Создаём глобальный менеджер сессий
session_manager = SessionManager()