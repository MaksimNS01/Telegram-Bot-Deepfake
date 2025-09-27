# Импорт библиотек
import asyncio # Для асинхронного программирования
import logging # Для ведения логов
from aiogram.filters.command import Command # Для обработки команд бота
from aiogram import F as FILETYPE # Для работы с типами файлов (as FILETYPE т.к. в tensorflow.nn исп-ся F и возникает конфликт)

# Импорт модулей
from app.bot import bot, dp # Экземпляры бота и диспетчера из модуля bot_init.py
from app.handlers import cmd_start, handle_image, set_gender, change_gender, show_menu, send_referral_link # Обработчики команд и сообщений из модуля handlers.py


# Включаем логирование и устанавливаем уровень логов на INFO
# Это позволит выводить сообщения уровня INFO и выше (например, WARNING, ERROR)
logging.basicConfig(level=logging.INFO)

# Регистрируем обработчики (хендлеры) для различных типов сообщений:
# Регистрация обработчика команды /start
dp.message.register(cmd_start, Command("start"))

# Регистрация обработчика для изображений
dp.message.register(handle_image, FILETYPE.photo)
# Регистрация обработчика для кнопок выбора пола
dp.callback_query.register(set_gender, lambda c: c.data in ['male', 'female'])
# Регистрация обработчика для команды /set_gender
dp.message.register(change_gender, Command("set_gender"))
# Регистрация обработчика для команды /menu
dp.message.register(show_menu, Command("menu"))
# Регистрация обработчика для команды /refer
dp.message.register(send_referral_link, Command('refer'))


# Асинхронная функция для запуска процесса поллинга новых апдейтов (сообщений) от пользователей
async def main():
    # Запуск поллинга
    await dp.start_polling(bot)

# Проверка, является ли данный скрипт основным модулем, который запущен
if __name__ == "__main__":
    try:
        # Запуск асинхронной функции main() с использованием asyncio.run()
        asyncio.run(main())
    except KeyboardInterrupt:
        # Обработка прерывания программы с клавиатуры (например, Ctrl+C)
        print('Бот отключён')