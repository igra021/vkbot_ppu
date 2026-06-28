# handlers\chat.py
# хендлеры сообщений

from vkbottle.bot import BotLabeler, Message
from llm.chat_gpt import chat_gpt
from config import vk_admin, verbose
# from create_bot import bot
chat_labeler = BotLabeler()
chat_labeler.vbml_ignore_case = True

@chat_labeler.message()
async def chat(message: Message):
    # Извлекаем текст
    
    result=''
    if message.text:
        result = await chat_gpt(message.text, verbose)


    # Извлекаем все фото
    photos = [att.photo for att in message.attachments if att.photo]
    # Извлекаем все видео
    videos = [att.video for att in message.attachments if att.video]
    
    # Формируем список строк для параметра attachment
    attachments = []
    for photo in photos:
        attachments.append(f"photo{photo.owner_id}_{photo.id}")
    for video in videos:
        attachments.append(f"video{video.owner_id}_{video.id}")

    """
    # Отправляем другому пользователю
    await bot.api.messages.send(
        peer_id=vk_admin,
        message=f"Вам пересылают вложения из чата: https://vk.com/im?peer={message.peer_id}",
        attachment=",".join(attachments),  # склеиваем через запятую
        random_id=0
    )
    """
    
    if attachments:
        result += "\n✅ Ваши фото и видео из сообщения пересланы администратору."

    return result
