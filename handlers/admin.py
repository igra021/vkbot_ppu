# handlers\admin.py
# Команды админа

from vkbottle.bot import BotLabeler, Message, rules
from db.database import clear_history
from config import vk_admin

admin_labeler = BotLabeler()
admin_labeler.auto_rules = [rules.FromPeerRule(vk_admin)] # Допустим, вы являетесь Павлом Дуровым

# команда /clear
@admin_labeler.message(command="clear")
async def halt(message: Message):
    await clear_history(message.from_id)
    print("------------ История очищена")
    await message.answer('История очищена')