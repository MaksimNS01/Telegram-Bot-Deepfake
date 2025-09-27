# Импорт библиотек
from aiogram import Bot, Dispatcher # Для создания бота и диспетчера
from aiogram.fsm.storage.memory import MemoryStorage # Для временного хранения данных в памяти во время работы приложения

from app.settings import API_TOKEN

# Создаем объект бота с использованием токена
bot = Bot(token=API_TOKEN)

# Создаем объект хранилища
storage = MemoryStorage()

# Создаем диспетчер для управления обновлениями от бота
dp = Dispatcher(storage=storage)