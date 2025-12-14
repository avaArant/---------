from pydantic_settings import BaseSettings
from typing import Optional


class StreamSettings(BaseSettings):
    # Настройки приложения
    APP_NAME: str = "Ozon FBO Streaming API"
    APP_VERSION: str = "2.0.0"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8001
    DEBUG: bool = False

    # Для тестов
    USE_MOCK: bool = False
    OZON_CLIENT_ID: Optional[str] = None
    OZON_API_KEY: Optional[str] = None

    # Логирование
    LOG_LEVEL: str = "INFO"

    # Потоковая обработка
    STREAM_CHUNK_SIZE: int = 10
    STREAM_TIMEOUT: int = 300
    STREAM_BUFFER_SIZE: int = 100

    # Rate limiting для потоков
    MAX_STREAMS_PER_CLIENT: int = 3
    STREAM_RATE_LIMIT_PER_MINUTE: int = 60

    # Кэширование Redis
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = True
    CACHE_TTL: int = 300
    CACHE_PREFIX: str = "ozon_stream"

    # Таймауты и повторные попытки
    CONNECTION_TIMEOUT: int = 10
    BACKOFF_FACTOR: float = 0.5

    # Защита от перегрузки
    MAX_REQUEST_SIZE_MB: int = 10
    RATE_LIMIT_PER_IP: int = 10

    # Валидация периода
    MAX_PERIOD_DAYS: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = StreamSettings()