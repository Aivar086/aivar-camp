FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Порт по умолчанию
ENV PORT=8000
EXPOSE 8000

# Запуск приложения
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
