# llm\text_cleaner.py
# очистка текста сообщения клиента от мусора

import re
import unicodedata

def clean_text(
    text: str,
    lower: bool = False,
    remove_emoji: bool = False,
    remove_punctuation: bool = False,
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
    
    # Удаляем пунктуацию (опционально)
    if remove_punctuation:
        text = re.sub(r'[^\w\s]', '', text)
    
    # Приводим к нижнему регистру
    if lower:
        text = text.lower()
    
    # Убираем множественные пробелы
    if remove_extra_spaces:
        text = re.sub(r'\s+', ' ', text)
    
    # Убираем пробелы по краям
    text = text.strip()
    
    return text


def normalize_text(text: str) -> str:
    """
    Нормализует текст для сравнения (убирает различия)
    """
    if not text:
        return ""
    
    # Приводим к нижнему регистру
    text = text.lower()
    
    # Убираем пунктуацию
    text = re.sub(r'[^\w\s]', '', text)
    
    # Убираем множественные пробелы
    text = re.sub(r'\s+', ' ', text)
    
    # Убираем пробелы по краям
    text = text.strip()
    
    return text


def truncate_text(text: str, max_length: int = 1000) -> str:
    """
    Обрезает текст до указанной длины
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def extract_keywords(text: str) -> list[str]:
    """
    Извлекает ключевые слова из текста (для поиска)
    """
    # Убираем стоп-слова (можно дополнить)
    stop_words = {'и', 'в', 'на', 'с', 'по', 'к', 'у', 'а', 'но', 'за'}
    
    # Очищаем текст
    clean = normalize_text(text)
    
    # Разбиваем на слова
    words = clean.split()
    
    # Фильтруем стоп-слова
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    
    return keywords


# Пример использования в хендлере
if __name__ == "__main__":
    test_text = "   Привет,   мир!!! 😊   Как   дела?   \n\t"
    
    print("Оригинал:", repr(test_text))
    print("Очищенный:", clean_text(test_text))
    print("Нормализованный:", normalize_text(test_text))
    print("Ключевые слова:", extract_keywords(test_text))