# handlers\chat.py
# хендлеры сообщений


from vkbottle.bot import BotLabeler, Message
from llm.chat_gpt import chat_gpt
from service.is_telephone import is_telephone
from service.text_cleaner import clean_text
from init.config import vk_admin
from loguru import logger
import json

chat_labeler = BotLabeler()
chat_labeler.vbml_ignore_case = True


async def send_to_admin(vk_admin, user_id, attachments, message):
    await message.ctx_api.messages.send(
    peer_id=vk_admin,
    message=f"Вложения от пользователя {user_id}:\n{attachments}",
    random_id=0
    )


@chat_labeler.message()
async def chat(message: Message):
    video_link = ''
    response = ''
    attachments = []

    try:
        user_id = message.from_id  # ✅ ID пользователя
        result = ''
        
        # Обработка текстового сообщения
        if message.text:
            # очистка сообщения клиента от мусора
            new_message = clean_text(message.text)
            # проверка на номер телефона в сообщении клиента
            new_message, telephone = is_telephone(new_message)
            if telephone.lstrip():
                # отправить админу телефон
                await send_to_admin(vk_admin, user_id, 'телефон: ' + telephone, message)

            # обращение к ЛЛМ
            if new_message:
                result = await chat_gpt(user_id, new_message)
            
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

        
        # Обработка вложений (фото, видео)
        photos = [att.photo for att in message.attachments if att.photo]
        videos = [att.video for att in message.attachments if att.video]
        
        for photo in photos:
            attachments.append(f"photo{photo.owner_id}_{photo.id}")
        for video in videos:
            attachments.append(f"video{video.owner_id}_{video.id}")
        
        if attachments:
            response += "\n\n✅ Ваши фото и видео пересланы администратору."

            # ✅ Отправка сообщения администратору, ошибка - в виде списка, а не в виде объектов
            await send_to_admin(vk_admin, user_id, attachments, message)

        
        # ✅ Отправляем сообщение в бот
        await message.answer(response)


        # ✅ Отправляем видео в бот
        if video_link:    
            await message.answer("Посмотрите видео по вашей ситуации: ", attachment=video_link)
        
        # Если очищенное сообщение пустое
        if not attachments and not new_message:
            response = "Пустое сообщение. Попробуйте переформулировать вопрос."

    except Exception as e:
        logger.error(f"❌ Ошибка в обработчике: {e}")
        await message.answer("Извините, произошла ошибка. Попробуйте позже.")
