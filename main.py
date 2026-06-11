# main.py

from config import create_bot
import asyncio

async def main():
       
    bot = create_bot()

    @bot.on.message()
    async def handler(message):
        print(f"Сообщение: {message.text}")
        user = await bot.api.users.get(user_ids=message.from_id)
        if user:
            await message.answer(f"Привет, {user[0].first_name}!")
        else:
            await message.answer("Привет!")
    
    print("Бот запущен")
    await bot.run_polling()

if __name__ == "__main__":
    asyncio.run(main())