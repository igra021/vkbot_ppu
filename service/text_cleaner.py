# llm\text_cleaner.py
# очистка текста сообщения клиента от мусора

import re
import unicodedata

def clean_text(
    text: str,
    remove_emoji: bool = True,
    remove_extra_spaces: bool = True,
    remove_control_chars: bool = True
) -> str:
    """
    Очищает текст от лишних символов
    
    Args:
        text: Исходный текст
        lower: Привести к нижнему регистру
        remove_emoji: Удалить эмодзи
        remove_punctuation: Удалить пунктуацию
        remove_extra_spaces: Убрать множественные пробелы
        remove_control_chars: Удалить управляющие символы
        
    Returns:
        Очищенный текст
    """
    if not text:
        return ""
    
    # Приводим к строке
    text = str(text)
    
    # Удаляем управляющие символы
    if remove_control_chars:
        text = ''.join(ch for ch in text if ch.isprintable() or ch.isspace())
    
    # Удаляем эмодзи (опционально)
    if remove_emoji:
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"  # смайлики
            u"\U0001F300-\U0001F5FF"  # символы и пиктограммы
            u"\U0001F680-\U0001F6FF"  # транспорт и карты
            u"\U0001F1E0-\U0001F1FF"  # флаги
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        text = emoji_pattern.sub(r'', text)
       
    # Убираем множественные пробелы
    if remove_extra_spaces:
        text = re.sub(r'\s+', ' ', text)
    
    # Убираем пробелы по краям
    text = text.strip()
    
    return text

