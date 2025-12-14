from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn
import logging
import time
from datetime import datetime
from contextlib import asynccontextmanager
import json

from config import settings
from routers import router as fbo_router

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Время запуска приложения
app_start_time = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Контекст жизненного цикла приложения"""
    logger.info("=" * 60)
    logger.info("Starting Ozon FBO Streaming Service...")
    logger.info(f"Application: {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Host: {settings.APP_HOST}:{settings.APP_PORT}")
    logger.info(f"Debug: {settings.DEBUG}")
    logger.info("=" * 60)

    yield

    # Завершение работы
    logger.info("Shutting down Ozon FBO Streaming Service...")

# Создание FastAPI приложения
app = FastAPI(
    title=settings.APP_NAME,
    description="Сервис потоковой обработки FBO отправлений из Ozon для интеграции с 1С",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Middleware для сжатия ответов
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(fbo_router, prefix="/api/v1/ozon", tags=["FBO Stream"])

@app.get("/", tags=["Root"])
async def root():
    """Корневой эндпоинт"""
    uptime = time.time() - app_start_time

    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    seconds = int(uptime % 60)
    uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "uptime": uptime_str,
        "current_time": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "api_root": "/api/v1/ozon",
            "fbo_postings": "/api/v1/ozon/fbo-postings",
            "status": "/api/v1/ozon/status",
            "docs": "/docs"
        }
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    uptime = time.time() - app_start_time

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "uptime_seconds": uptime
    }

# Глобальный обработчик исключений
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик исключений"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    error_message = str(exc)
    if hasattr(exc, 'detail'):
        error_message = exc.detail

    return Response(
        content=json.dumps({
            "error": "Internal server error",
            "message": error_message,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }),
        status_code=500,
        media_type="application/json"
    )

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )




