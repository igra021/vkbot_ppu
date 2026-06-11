# проверка работы бота - отправка сообщения ping

from config import bot

@bot.on.message(text="ping")
async def ping_handler(message):
    await message.answer("pong")