# команды доступные только админу

from vkbottle.bot import BotLabeler, Message, rules
from config import vk_admin

# BotLabeler - это "контейнер" для группы хендлеров. 
# Все обработчики, привязанные к этому лейблеру, будут иметь общее поведение (например, доступны только админу). 
# Это удобно для разделения логики: admin_labeler для команд управления
admin_labeler = BotLabeler()

# список правил, которые будут применяться к каждому хендлеру этого лейблера автоматически
admin_labeler.auto_rules = [rules.FromPeerRule(vk_admin)]

@admin_labeler.message(command="halt")
async def halt(_):
    exit(0)