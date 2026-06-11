# bot_create.py
# Создаёт бота

def create_bot():
    """Фабричная функция для создания бота (вызывается внутри event loop)"""
    
    # Создаём connector с отключением SSL-проверки для Windows
    connector = aiohttp.TCPConnector(ssl=False)
    
    if proxy:
        # Создаём HTTP-клиент с прокси
        http_client = AiohttpClient(connector=connector, proxy=proxy)
    else:
        http_client = AiohttpClient(connector=connector)
    
    # Создаём API с HTTP-клиентом
    api = API(token=token, http_client=http_client)
    
    # Создаём и возвращаем бота
    return Bot(api=api)