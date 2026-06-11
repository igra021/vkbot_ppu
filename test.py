token = "vk1.a.rAhZ0I-H7tpy8I9ltcsIos26yoJeFfiCuZuj4NaE58qMdWpb3F6QYLj2712mOkeKs1yBQnCesEE0RWxeqimnSSOcOnuVqa3hL2U6rzN7nwPBSjDlt03gVFUvdYVRP6gWEiYDOzCLX7yyMfSHpM8tjb8ZyGOsn5krCpIaEKX1VIRC056XMp9_UOaHQ1qhIGjamakh_VRhCQ1XTosCEEZ0Sw"
token2 = 'vk1.a.MxRGx61GOl2lV_m3WZ4Ya9Atc-3PN2TVGWQwMZJYygXo2Z2KSEq-TjE6BhjMSIny7KDSbXuzfI9Fj1L_wxkSAAdBzQ2DJA0PxOPZi_7y-_hXallCEGVwI9OPcr83nnH0PyqUAigNdKuUHm4B7roZFJvWYTb7L-NaLzcmXdVYIuDu54ptrgJYhINJhdnd8c6zbEXLlonD-rMl9_VWcELhBA'
import asyncio
from loguru import logger
from vkbottle.bot import Bot, Message

bot = Bot(token=token2)
logger.info("Бот инициализирован")


async def get_group_info():
    print(await bot.api.groups.get_by_id())
    print(await bot.api.groups.get_members())

# Замените bot.run_forever() на:
asyncio.run(get_group_info())

@bot.on.message(text='test')
async def hi_handler(message: Message):
    logger.info(f"Получено сообщение от {message.from_id}: {message.text}")
    users_info = await bot.api.users.get(message.from_id)
    await message.answer("Привет, {}".format(users_info[0].first_name))
    logger.info("Ответ отправлен")

logger.info("Запуск бота...")
# bot.run_forever()
