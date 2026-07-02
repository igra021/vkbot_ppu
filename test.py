# diagnostic.py
from vkbottle import Bot
import inspect

# Выводим все параметры конструктора Bot
signature = inspect.signature(Bot.__init__)
for param_name, param in signature.parameters.items():
    print(f"{param_name}: {param.default}")
    
