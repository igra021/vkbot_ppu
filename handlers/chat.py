# handlers\chat.py
# хендлеры сообщений

from vkbottle.bot import BotLabeler, Message
from llm.chat_gpt import chat_gpt
chat_labeler = BotLabeler()
chat_labeler.vbml_ignore_case = True

@chat_labeler.message()
async def chat(message: Message):
    # Извлекаем текст
    text = message.text or ""
    result = chat_gpt(text)

    # Извлекаем все фото
    photos = [att.photo for att in message.attachments if att.photo]
    
    # Извлекаем все видео
    videos = [att.video for att in message.attachments if att.video]
    
    # Формируем ответ
    response_parts = []
    
    if text:
        response_parts.append(f"Текст: {text}")
    
    if photos:
        response_parts.append(f"Фото: {len(photos)} шт.")
        # Можно добавить URL первого фото
        if photos:
            response_parts.append(f"URL первого фото: {photos[0].sizes[-1].url}")
    
    if videos:
        response_parts.append(f"Видео: {len(videos)} шт.")
        if videos:
            response_parts.append(f"Видео: https://vk.com/video{videos[0].owner_id}_{videos[0].id}")

    await result
    # await message.answer("\n".join(response_parts))