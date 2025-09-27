# Импорт библиотек
import os # Стандартный модуль os для работы с операционной системой (например, для работы с файлами и директориями)
import logging # Для ведения логов
import asyncio # Для асинхронного программирования
from aiogram import types # Для работы с типами данных, используемыми в aiogram
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import time # Таймер
import psutil # Для получения информации о системе и процессах
import sqlite3 # Для работы с БД

from collections import deque # Для двусторонняя очередь
from aiogram.types import InputSticker # Для создания нового стикера или набора стикеров в Telegram
from aiogram.types.input_file import FSInputFile # Для отправки файлов, хранящихся на файловой системе, в Telegram
from aiogram.utils.media_group import MediaGroupBuilder # Для для создания и отправки медиа-групп (альбомов) в Telegram
from aiogram.methods import CreateNewStickerSet # Для создания нового набора стикеров в Telegram

# Экземпляр бота из модуля bot_init.py
from .bot import bot
from app.settings import CHANNEL_ID

# Импорт функций из модуля functions.py
from .functions import (
    check_and_delete_file,    # Функция для проверки и удаления файла
    detect_selfie, # Функция для проверки наличия четкого лица на фото
    faceswap, # Функция для замены лица
    convert_to_sticker, # Функция преобразования изображений в необходимый для создания стикеров формат (WEBP 512x512)
    generate_referral_link, # Функция генерации реферальной ссылки
    create_connection # Функция создания подключения с БД
)

# Подключение к БД
conn = sqlite3.connect('./referrals.db')
cursor = conn.cursor()
# Создание таблицы users
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    attempts INTEGER DEFAULT 100
                  )''')
# Создание таблицы referrals
cursor.execute('''CREATE TABLE IF NOT EXISTS referrals (
                    referral_id TEXT PRIMARY KEY,
                    referrer_id INTEGER,
                    FOREIGN KEY (referrer_id) REFERENCES users (user_id)
                  )''')
# Отключение от БД
conn.commit()
conn.close()

# Очередь для хранения результатов последних 1000 запросов
last_10_processing_times = deque(maxlen=1000)
last_10_memory_usages = deque(maxlen=1000)

# Клавиатура для выбора пола
kb_list = [
    [InlineKeyboardButton(text='Мужской', callback_data='male')],
    [InlineKeyboardButton(text='Женский', callback_data='female')]
]
gender_keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list, row_width=2)

# Клавиатура для кнопки "Подписаться"
channel_url = 'https://t.me/tvrussia1'
subscribe_list = [[InlineKeyboardButton(text='Подписаться', url=channel_url)]]
subscribe_keyboard = InlineKeyboardMarkup(inline_keyboard=subscribe_list, row_width=1)

# Переменная для хранения выбранного пола
user_gender = {}


# Хэндлер для команды /menu
async def show_menu(message: types.Message):
    await message.reply("Доступные команды:\n"
                        "/start - Старт\n"
                        "/set_gender - Изменить пол"
                        "/refer - Получить реферальную ссылку")

async def send_referral_link(message: types.Message):
    user_id = message.from_user.id
    referral_link = generate_referral_link(user_id)
    await message.reply(f"Ваша реферальная ссылка: {referral_link}", disable_web_page_preview = True)

# Хэндлер для команды /start
async def cmd_start(message: types.Message):
    args = message.text.split()
    user_id = message.from_user.id
    conn = create_connection()
    cursor = conn.cursor()

    # Проверка, если пользователь уже существует
    cursor.execute('SELECT attempts FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute('INSERT INTO users (user_id, attempts) VALUES (?, ?)', (user_id, 100))
        conn.commit()
    
    if len(args) > 1:
        referral_id = args[1]

        cursor.execute('SELECT referrer_id FROM referrals WHERE referral_id = ?', (referral_id,))
        referrer = cursor.fetchone()
        if referrer:
            referrer_id = referrer[0]
            cursor.execute('SELECT attempts FROM users WHERE user_id = ?', (referrer_id,))
            user = cursor.fetchone()
            if user:
                attempts = user[0] + 1
                cursor.execute('UPDATE users SET attempts = ? WHERE user_id = ?', (attempts, referrer_id))
                conn.commit()
                referrer_message = f"Поздравляю! Ваш друг присоединился к нам!\n\nБлагодаря Вашему приглашению, к нам присоединился новый участник исторического путешествия. В награду за распространение культурного наследия вам начислена дополнительная обработка!\n\nТекущий баланс доступных обработок: {attempts}.\n\nХотите использовать новую обработку прямо сейчас? Отправьте мне свое фото!\n\nПродолжайте приглашать друзей и получайте еще больше возможностей создать свой неповторимый образ в эпохе Александра I."
                await bot.send_message(referrer_id, referrer_message)
    conn.close()
    referral_link = generate_referral_link(user_id)
    # Отправляем ответное сообщение пользователю
    await message.answer('Приветствую вас в эпохе великих свершений! Я — бот сериала "Александр I".\n\nЧтобы начать путешествие во времени, необходимо подписаться на [официальный телеграм-канал России 1](https://t.me/tvrussia1). Проверю вашу подписку...', disable_web_page_preview = True, parse_mode="MARKDOWN", reply_markup=subscribe_keyboard)
    await asyncio.sleep(1)
    await check_subscription(user_id, message.chat.id)

# Функция проверки подписки
async def check_subscription(user_id: int, chat_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            await bot.send_message(chat_id, "Вы подписаны на канал! Выберите пол:", reply_markup=gender_keyboard)
        else:
            await bot.send_message(chat_id, "Пожалуйста, подпишитесь на наш канал, чтобы продолжить.")
    except Exception as e:
        await bot.send_message(chat_id, "Не удалось проверить подписку.")

# Хэндлер для команды /set_gender
async def change_gender(message: types.Message):
    # Отправляем ответное сообщение пользователю
    await message.answer("Выберите пол:", reply_markup=gender_keyboard)

# Хэндлер на кнопки выбора пола
async def set_gender(callback_query: types.CallbackQuery):
    gender = 'Мужской' if callback_query.data == 'male' else 'Женский'
    user_gender[callback_query.from_user.id] = gender
    await bot.answer_callback_query(callback_query.id)
    # Таймер на 1 секунды
    await asyncio.sleep(1)
    await bot.send_message(callback_query.from_user.id, "Прекрасно! Теперь отправьте мне свое фото, на котором хорошо видно ваше лицо.\n\nРекомендации для идеального результата:\n• Лицо должно быть хорошо освещено\n• Без солнцезащитных очков и головных уборов\n• Смотрите прямо в камеру\n• Фото должно быть четким\n• Только человеческие лица (фото животных не обрабатываются)\n\nЯ жду ваше фото, чтобы превратить вас в героя истории!")

# Хэндлер для обработки изображений
async def handle_image(message: types.Message):
    user_id = message.from_user.id
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT attempts FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    # Устанавливаем статус бота "Отправляет фото..."
    await message.bot.send_chat_action(message.chat.id, 'upload_photo')
    try:
        process = psutil.Process()
    
        # Измерение начальных значений ресурсов
        start_memory = process.memory_info().rss
        start_time = time.time()
        
        # Получаем file_id последнего фото из сообщения
        file_id = message.photo[-1].file_id
        
        # Получаем информацию о файле по его file_id
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path

        # Устанавливаем путь для сохранения входного изображения
        input_path = os.path.join('temp_images', f"{file_id}.jpg")

        # Проверяем и удаляем файл, если он уже существует
        check_and_delete_file(input_path)
        
        # Скачиваем файл по file_path и сохраняем его в input_path
        await bot.download_file(file_path, input_path)

        # Проверка, не превышает ли пользователь лимит
        if user and user[0] > 0:
            if detect_selfie(input_path):
                if user_id in user_gender:
                    gender = user_gender[user_id]
                    if gender == "Мужской":
                        result_image_paths = faceswap(input_path, 'stock_images/M', 'result_images/')
                    elif gender == "Женский":
                        result_image_paths = faceswap(input_path, 'stock_images/W', 'result_images/')
                else:
                    await message.answer("Пол не выбран. Пожалуйста, выберите пол с помощью команды /set_gender.")
                    
                # Отправляем пользователю изображение
                media_group = MediaGroupBuilder()
                for rip in result_image_paths:
                    media_group.add_photo(media=FSInputFile(rip))
                attempts = user[0]
                print(f"\n\nДо {attempts}")
                attempts = user[0] - 1
                print(f"После {attempts}\n\n")
                cursor.execute('UPDATE users SET attempts = ? WHERE user_id = ?', (attempts, user_id))
                conn.commit()
                referral_link = generate_referral_link(user_id)
                
                await message.answer(f"Великолепно! Ваш исторический образ готов!\n\n🖼️ Вот ваши результаты:\n• Постер сериала с вашим участием\n• Ваш исторический портрет\n• Набор эксклюзивных стикеров для Telegram\n\nСохраните их и поделитесь с друзьями! Не забудьте использовать хештег #АлександрПервый и отметить телеканал Россия 1  в социальных сетях.\n\nХотите создать еще один образ? Кол-во оставшихся обработок: {attempts}!")
                await bot.send_media_group(chat_id=message.chat.id, media=media_group.build())

                stickers_paths = []

                for rip in result_image_paths:
                    # Конвертируем `photo.jpg` в `photo.png` (в той же папке)
                    stick = convert_to_sticker(rip)
                    stickers_paths.append(stick)

                print(f'Созданы стикеры: {stickers_paths}')
                
                # Удаляем входное и выходное изображения для очистки памяти
                check_and_delete_file(input_path)
                for rip in result_image_paths:
                    check_and_delete_file(rip)
                                        
                stickers = [InputSticker(sticker=FSInputFile(stickers_imgs), format='static', emoji_list=['😀']) for stickers_imgs in stickers_paths]

                # Создаем новый стикерпак
                sticker_pack_name = f"z{stickers_paths[1][19:][:-5]}{user_id}_by_deep_fake_test_bot"
                print(sticker_pack_name)
                result = await bot(CreateNewStickerSet(
                    user_id=user_id,
                    name=sticker_pack_name,
                    title="Александр 1 стикеры тут: @tvrussia1",
                    stickers=stickers,
                    sticker_type='regular'
                ))

                if result:
                    sticker_pack_url = f"https://t.me/addstickers/{sticker_pack_name}"
                    await message.reply(f"Стикерпак успешно создан!\nЧтобы добавить его, перейди по [ссылке]({sticker_pack_url})", parse_mode="MARKDOWN")
                else:
                    await message.reply("Не удалось создать стикерпак.")  

                for sticks in stickers_paths:
                    check_and_delete_file(sticks)     
            else:
                await message.answer("Кажется, что-то пошло не так! Я не смог распознать лицо на этой фотографии.\n\nВозможные причины:\n• На фото нет четко видимого лица\n• Лицо закрыто (очки, маска, головной убор)\n• Слишком темное или размытое изображение\n• На фото животное или другой объект\n\nПожалуйста, отправьте другое фото, где ваше лицо хорошо видно. Помните, что качество результата напрямую зависит от качества исходного фото!")
        else:
            referral_link = generate_referral_link(user_id)
            await message.answer(f"Ваши 3 бесплатные обработки использованы! Но история на этом не заканчивается...\n\nХотите получить еще больше исторических образов? Пригласите друзей присоединиться к нашему путешествию во времени!\n\nКак получить дополнительные обработки:\n1. Отправьте друзьям вашу персональную ссылку: {referral_link}\n2. За каждого друга, который подпишется на канал России 1 и воспользуется ботом, вы получите +1 новую обработку\n3. Количество приглашенных друзей не ограничено!\n\nПоделитесь своими историческими образами в социальных сетях с хештегом #АлександрПервый и не забудьте отметить телеканал Россия 1!", disable_web_page_preview = True)

        # Измерение конечных значений ресурсов
        end_time = time.time()
        end_memory = process.memory_info().rss
          
        # Вычисление затрат времени и ресурсов
        processing_time = end_time - start_time
        memory_usage = end_memory - start_memory

        print(f"Время обработки одной картинки: {processing_time} секунд")
        print(f"Использование памяти: {memory_usage / (1024 * 1024)} MB")

        # Обновление очередей
        last_10_processing_times.append(processing_time)
        last_10_memory_usages.append(memory_usage)
            
        # Вычисление средних значений
        avg_processing_time = sum(last_10_processing_times) / len(last_10_processing_times)
        avg_memory_usage = sum(last_10_memory_usages) / len(last_10_memory_usages)
        print(f"Среднее время обработки последних 10 картинок: {avg_processing_time} секунд")
        print(f"Среднее использование памяти последних 10 картинок: {avg_memory_usage / (1024 * 1024)} MB")  

    except Exception as e:
        # Логируем ошибку и отправляем сообщение об ошибке пользователю
        logging.error(f"Error processing image: {e}")
        await message.answer("Произошла ошибка при обработке изображения.")
    # Удаляем входное и выходное изображения для очистки памяти
    check_and_delete_file(input_path)
    for rip in result_image_paths:
        check_and_delete_file(rip)
    for sticks in stickers_paths:
        check_and_delete_file(sticks)
    
    conn.close()
