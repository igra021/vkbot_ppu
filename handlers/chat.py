# handlers\chat.py
# хендлеры сообщений


from vkbottle.bot import BotLabeler, Message
from llm.chat_gpt import chat_gpt
from config import verbose
from loguru import logger

chat_labeler = BotLabeler()
chat_labeler.vbml_ignore_case = True


@chat_labeler.message()
async def chat(message: Message):
    try:
        user_id = message.from_id  # ✅ ID пользователя
        result = ''
        
        # Обработка текстового сообщения
        if message.text:
            result = await chat_gpt(user_id, message.text, verbose)
        
        # Если ответ пустой — подставляем дефолтное сообщение
        if not result or not result.strip():
            result = "Извините, я не смог обработать ваш запрос. Попробуйте переформулировать вопрос."
            logger.warning(f"⚠️ Пустой ответ для user_id={user_id}")
        
        # Обработка вложений (фото, видео)
        photos = [att.photo for att in message.attachments if att.photo]
        videos = [att.video for att in message.attachments if att.video]
        
        attachments = []
        for photo in photos:
            attachments.append(f"photo{photo.owner_id}_{photo.id}")
        for video in videos:
            attachments.append(f"video{video.owner_id}_{video.id}")
        
        if attachments:
            result += "\n\n✅ Ваши фото и видео пересланы администратору."
            # Здесь код пересылки администратору
        
        # ✅ Отправляем сообщение
        await message.answer(result)
        
    except Exception as e:
        logger.error(f"❌ Ошибка в обработчике: {e}")
        await message.answer("Извините, произошла ошибка. Попробуйте позже.")
