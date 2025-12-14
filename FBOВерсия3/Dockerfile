## Упрощенный Dockerfile
#FROM python:3.11-slim
#
#WORKDIR /app
#
## Копирование зависимостей
#COPY requirements.txt .
#
## Установка Python зависимостей
#RUN pip install --no-cache-dir -r requirements.txt
#
## Копирование остальных файлов проекта
#COPY . .
#
#EXPOSE 8000
#
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY src ./src/

# Создание .env если его нет
RUN if [ ! -f .env ]; then \
    echo "APP_NAME=Ozon FBO Service" > .env && \
    echo "DEBUG=false" >> .env; \
    fi

EXPOSE 8001

CMD ["python", "-m", "src.main"]