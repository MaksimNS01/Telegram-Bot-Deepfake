# Импорт библиотек
import os # Стандартный модуль os для работы с операционной системой (например, для работы с файлами и директориями)
import tensorflow as tf # Для машинного и глубокого обучения
import numpy as np # Для работы с массивами и числовыми операциями
import cv2 # Компьютерное зрение
import uuid # Для получения User ID
import sqlite3 # Для БД

from PIL import Image # Для работы с изображениями
from tensorflow.keras.preprocessing import image # Для работы с изображениями, включая загрузку и предварительную обработку
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions # Ддля работы с массивами и числовыми операциями

from ff_inference import face_fusion_swap # Импортируем инференс Face Fusion
from app.settings import YOUR_BOT_ID


# Загрузка предобученной модели MobileNetV2 с весами, обученными на наборе данных ImageNet
model = tf.keras.applications.MobileNetV2(weights='imagenet')


# Функция проверки существования файлов и их удаления 
def check_and_delete_file(file_path):
    if os.path.exists(file_path):  # Проверяем, существует ли файл по указанному пути
        os.remove(file_path)  # Удаляем файл, если он существует
        print(f"Файл {file_path} был удален.")  # Выводим сообщение о том, что файл был удален
    else:
        print(f"Файл {file_path} не существует.")  # Выводим сообщение, что файл не найден

# Функция классификации изображения и проверки его на наличие заблокированных меток
def classify_and_check_image(img_path, blocked_labels, FILTER_VOLUME):
    """
    Классифицирует изображение и проверяет его на наличие заблокированных меток.
    :param img_path: Путь к изображению.
    :param blocked_labels: Список меток, которые считаются заблокированными.
    :param FILTER_VOLUME: Количество топовых предсказаний, которые нужно учитывать.
    :return: True, если изображение безопасное, и False, если содержит заблокированные метки.
    """
    # Загрузка и предобработка изображения
    img = image.load_img(img_path, target_size=(224, 224))  # Загружаем изображение и изменяем его размер
    img_array = image.img_to_array(img)  # Преобразуем изображение в массив
    img_array = np.expand_dims(img_array, axis=0)  # Добавляем дополнительное измерение для пакета
    img_array = preprocess_input(img_array)  # Предобрабатываем изображение для модели

    # Классификация изображения
    predictions = model.predict(img_array)  # Делаем предсказание модели
    decoded_predictions = decode_predictions(predictions, top=FILTER_VOLUME)[0]  # Декодируем предсказания

    # Проходим по декодированным предсказаниям
    for i, (imagenet_id, label, score) in enumerate(decoded_predictions):
        print(f"{i+1}: {label} ({score:.2f})")  # Выводим метку и оценку предсказания
        if label in blocked_labels:  # Проверяем, есть ли метка в списке заблокированных
            return False  # Возвращаем False, если метка заблокирована
    return True  # Возвращаем True, если ни одна из меток не заблокирована

# Функция для проверки наличия четкого лица на фото
def detect_selfie(img_path):
    # Загрузка изображения
    img = cv2.imread(img_path)

    # Преобразование изображения в серый цвет
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Загрузка классификатора для распознавания лиц
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Распознавание лиц на изображении
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)

    if len(faces) > 0:
        return True
    else:
        return False

# Функция для замены лица
def faceswap(input_path, target_path, output_path):      
    # Загрузка шаблонных изображений
    stock_images = [os.path.join(target_path, img) for img in os.listdir(target_path) if img.endswith(('jpg', 'jpeg', 'png'))]
    result_image_paths = []
    for target_path in stock_images:
        try:
            result_image_path = face_fusion_swap(input_path, target_path, output_path)
            result_image_paths.append(result_image_path)
        except Exception as e:
            print(f"Ошибка обработки изображения {target_path}: {e}")
    
    return result_image_paths

# Функция преобразования изображений в необходимый для создания стикеров формат (WEBP 512x512)
def convert_to_sticker(input_path: str, output_dir: str = None) -> str:
    """
    Конвертирует изображение в валидный стикер для Telegram (WEBP 512x512).
    
    :param input_path: Путь к исходному изображению (JPG/PNG/etc)
    :param output_dir: Папка для сохранения (если None - рядом с исходным файлом)
    :return: Путь к .webp файлу
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Файл {input_path} не найден!")

    # Готовим имя выходного файла
    filename = os.path.splitext(os.path.basename(input_path))[0] + ".webp"
    output_path = os.path.join(output_dir or os.path.dirname(input_path), filename)

    # Открываем и обрабатываем изображение
    with Image.open(input_path) as img:
        # Конвертируем в RGBA (для прозрачности)
        img = img.convert("RGBA")

        # Получаем размеры изображения
        width, height = img.size

        # Находим размер стороны квадрата
        size = min(width, height)

        # Находим координаты для обрезки
        left = (width - size) // 2
        top = (height - size) // 2
        right = left + size
        bottom = top + size

        # Обрезаем изображение до квадрата
        img = img.crop((left, top, right, bottom))
        
        # Ресайз до 512x512 с сохранением пропорций (обрезает лишнее)
        img.thumbnail((512, 512))
        canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        canvas.paste(
            img,
            ((512 - img.width) // 2, (512 - img.height) // 2)
        )
        
        # Сохраняем как WEBP с оптимизацией
        canvas.save(
            output_path,
            "WEBP",
            quality=90,
            method=6,  # Максимальное сжатие
            lossless=False
        )

    return output_path

# Функция генерации реферальной ссылки
def generate_referral_link(user_id):
    referral_id = str(uuid.uuid4())
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO referrals (referral_id, referrer_id) VALUES (?, ?)', (referral_id, user_id))
    conn.commit()
    conn.close()
    return f"https://t.me/{YOUR_BOT_ID}?start={referral_id}"

# Функция создания подключения с БД
def create_connection():
    return sqlite3.connect('./referrals.db')