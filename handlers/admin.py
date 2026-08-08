# handlers/admin.py
# Команды админа

from vkbottle.bot import BotLabeler, Message, rules
from db.database import clear_history_db
from config import vk_admin
from session_manager import session_manager  # ✅ Импортируем менеджер сессий

admin_labeler = BotLabeler()
admin_labeler.auto_rules = [rules.FromPeerRule(vk_admin)]

# команда /clear
@admin_labeler.message(command="clear")
async def clear_command(message: Message):
    user_id = message.from_id
    
    # 1. Очищаем историю в БД
    await clear_history_db(user_id)
    
    # 2. Очищаем сессию в памяти
    session_manager.clear_session(user_id)
    
    await message.answer('✅ История и сессия очищены')