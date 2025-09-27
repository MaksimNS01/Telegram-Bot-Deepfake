# Используем официальный образ Python в качестве базового образа
FROM python:3.12-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл requirements.txt в рабочую директорию
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта в рабочую директорию
COPY . .

# Устанавливаем переменные окружения (если необходимо)
# ENV VARIABLE_NAME=value

# Указываем команду для запуска вашего приложения
CMD ["python", "main.py"]
