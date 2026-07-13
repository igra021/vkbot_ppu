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
        self._cleanup_expired()
        
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
            self._save_and_remove(uid)
        
        if expired:
            logger.debug(f"🗑️ Удалено {len(expired)} истекших сессий")
    
    def _save_and_remove(self, user_id: int):
        """Сохраняет dirty-сессию и удаляет"""
        session = self.sessions.get(user_id)
        if session and session.is_dirty:
            # TODO: Сохранить в БД
            # await save_history(user_id, session.history)
            logger.debug(f"💾 Сохранена сессия для {user_id}")
        
        del self.sessions[user_id]
    
    def save_all(self):
        """Сохраняет все dirty-сессии"""
        for user_id, session in self.sessions.items():
            if session.is_dirty:
                # TODO: Сохранить в БД
                # await save_history(user_id, session.history)
                pass
    
    def clear_session(self, user_id: int):
        """Очищает сессию пользователя"""
        if user_id in self.sessions:
            del self.sessions[user_id]
            logger.info(f"🗑️ Сессия {user_id} очищена")

# Создаём глобальный менеджер сессий
session_manager = SessionManager()