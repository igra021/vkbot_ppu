# service\is_telephone.py
# поиск телефона в сообщении клиента
import phonenumbers
from phonenumbers import PhoneNumberMatcher

def is_telephone(text):

    """
    Заменяет все найденные номера на один статичный фальшивый
    """
    fake_number="+79120000000"
    # Собираем все найденные номера с их позициями
    matches = list(PhoneNumberMatcher(text, "RU"))

    if not matches:
        return text
    
    # Заменяем с конца, чтобы не сбивать индексы
    result = text
    for match in reversed(matches):
        print(match.raw_string)
        start = match.start
        end = match.end
        result = result[:start] + fake_number + result[end:]
    
    return result
