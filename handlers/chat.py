# handlers\chat.py
# хендлеры сообщений


from vkbottle.bot import BotLabeler, Message
from llm.chat_gpt import chat_gpt
from loguru import logger
import json

chat_labeler = BotLabeler()
chat_labeler.vbml_ignore_case = True


@chat_labeler.message()
async def chat(message: Message):
    # проверка работы чатбота- сообщения доходят до бота
    # print(f"🔥 ПОЛУЧЕНО СООБЩЕНИЕ от {message.from_id}: {message.text}")

    try:
        user_id = message.from_id  # ✅ ID пользователя
        result = ''
        
        # Обработка текстового сообщения
        if message.text:

            # result — это строка JSON, ответ от LLM
            result = await chat_gpt(user_id, message.text)
            if result:
                try:
                    data = json.loads(result)
                    response = data.get('response', '')
                    video_link = data.get('video', '')

                except json.JSONDecodeError:
                    response = result  # fallback, если не JSON
            else:
                response = ''
        else:
            response = ''

        # Если ответ пустой — дефолтное сообщение
        if not response or not response.strip():
            response = "Извините, я не смог обработать ваш запрос. Попробуйте переформулировать вопрос."
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
            response += "\n\n✅ Ваши фото и видео пересланы администратору."
            # Здесь код пересылки администратору
        
        # ✅ Отправляем сообщение в бот
        await message.answer(response)


        # ✅ Отправляем видео в бот
        if video_link:    
            await message.answer("Посмотрите видео по вашей ситуации: ", attachment=video_link)
        
    except Exception as e:
        logger.error(f"❌ Ошибка в обработчике: {e}")
        await message.answer("Извините, произошла ошибка. Попробуйте позже.")
