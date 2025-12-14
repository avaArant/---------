import uuid
from datetime import datetime
from typing import Optional
import logging

from fastapi import APIRouter, HTTPException, Header
from src.models.schemas import FBORequest
from src.services.service_factory import OzonServiceFactory

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/fbo-postings", summary="Получение FBO отправлений для 1С")
async def get_fbo_postings(
        request: FBORequest,
        client_id: Optional[str] = Header(None, alias="Client-Id"),
        api_key: Optional[str] = Header(None, alias="Api-Key")
):
    """Основной эндпоинт"""
    logger.info(f"FBO request: {request.period_from} - {request.period_to}")

    # 1. Валидация заголовков
    if not client_id or not api_key:
        raise HTTPException(
            status_code=401,
            detail="Укажите Client-Id и Api-Key в заголовках"
        )

    # 2. Валидация периода
    try:
        period_from = datetime.fromisoformat(request.period_from.replace('Z', ''))
        period_to = datetime.fromisoformat(request.period_to.replace('Z', ''))

        if period_from > period_to:
            raise HTTPException(
                status_code=400,
                detail="Начало периода позже окончания"
            )

        period_days = (period_to - period_from).days
        if period_days > 30:
            raise HTTPException(
                status_code=400,
                detail="Период не может превышать 30 дней"
            )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Неверный формат даты. Используйте формат: YYYY-MM-DDTHH:MM:SS"
        )

    # 3. Создание сервиса
    request_id = str(uuid.uuid4())[:8]
    service = OzonServiceFactory.create_service(
        client_id=client_id.strip(),
        api_key=api_key.strip(),
        request_id=request_id
    )

    all_postings = []
    total_postings = 0

    try:
        # 4. Получение данных
        async with service:
            async for posting_batch in service.stream_postings(
                    period_from=period_from,
                    period_to=period_to
            ):
                # Преобразуем в словари
                for posting in posting_batch:
                    if hasattr(posting, 'dict'):
                        all_postings.append(posting.dict())
                    else:
                        all_postings.append(posting)
                total_postings += len(posting_batch)

                logger.info(f"[{request_id}] Батч: {len(posting_batch)}, всего: {total_postings}")

        # 5. Формируем JSON строку ВРУЧНУЮ!
        import json

        response_dict = {
            "success": True,
            "message": "Success",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "отправления": all_postings[:5] if all_postings else [],
                "статистика": {
                    "всего_отправлений": len(all_postings[:5]),
                    "обработано": len(all_postings[:5])
                }
            },
            "metadata": {
                "request_id": request_id,
                "period": {
                    "from": request.period_from,
                    "to": request.period_to
                },
                "client_id": client_id[:8] + "..." if client_id else None,
                "обработано_отправлений": len(all_postings[:5]),
                "всего_найдено": total_postings
            },
            "errors": [],
            "warnings": []
        }

        # Явно сериализуем в JSON
        json_str = json.dumps(
            response_dict,
            ensure_ascii=False,
            default=str,
            indent=None
        )

        logger.info(f"[{request_id}] JSON string length: {len(json_str)}")
        logger.info(f"[{request_id}] First 200 chars: {json_str[:200]}")

        # Возвращаем Response с JSON строкой
        from fastapi.responses import Response
        return Response(
            content=json_str,
            media_type="application/json; charset=utf-8",
            status_code=200
        )

    except Exception as e:
        logger.error(f"[{request_id}] Ошибка: {e}", exc_info=True)

        import json
        error_dict = {
            "success": False,
            "message": "Error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "data": None,
            "metadata": {"request_id": request_id},
            "errors": [{"message": str(e)}],
            "warnings": []
        }

        error_json = json.dumps(error_dict, ensure_ascii=False, default=str)

        from fastapi.responses import Response
        return Response(
            content=error_json,
            media_type="application/json; charset=utf-8",
            status_code=500
        )


@router.post("/test-simple")
async def test_simple():
    """Простейший тестовый эндпоинт"""
    response_data = {
        "success": True,
        "message": "Test",
        "timestamp": datetime.now().isoformat()
    }

    logger.info(f"Test response type: {type(response_data)}")
    logger.info(f"Test response: {response_data}")

    return response_data


@router.get("/status", summary="Статус сервиса")
async def get_service_status():
    """Простой статус"""
    from src.config import settings

    status_data = {
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

    return status_data


@router.get("/test", summary="Тест подключения")
async def test_connection():
    """Простой тест подключения"""
    test_data = {
        "success": True,
        "message": "API доступен",
        "timestamp": datetime.now().isoformat()
    }

    return test_data


# ДОБАВЬТЕ этот эндпоинт (GET версия)
@router.get("/test-all-formats-get")
async def test_all_formats_get():
    """Тестовый эндпоинт с разными форматами (GET версия)"""

    tests = {
        "test1": {
            "success": True,  # boolean
            "message": "Test with boolean success"
        },
        "test2": {
            "success": 1,  # integer
            "message": "Test with integer success"
        },
        "test3": {
            "success": "true",  # string
            "message": "Test with string success"
        },
        "test4": {
            "success": "True",  # string with capital
            "message": "Test with string True"
        },
        "test5": {  # Самый простой
            "test": "value"
        },
        "test6": "just string",  # Только строка
        "test7": 123,  # Только число
        "test8": True,  # Только boolean
        "test9": None  # Null
    }

    return {
        "timestamp": datetime.now().isoformat(),
        "tests": tests,
        "note": "1С должен видеть эту структуру как объект"
    }


@router.post("/test-for-1c")
async def test_for_1c(format_type: str = "json"):
    """Специальный тест для 1С с разными форматами"""

    import json

    formats = {
        "simple": {"result": "success", "count": 1},
        "nested": {
            "success": True,
            "data": {"items": [1, 2, 3]},
            "meta": {"page": 1}
        },
        "array": [1, 2, 3, 4, 5],
        "string": "Just a string response",
        "number": 42,
        "boolean": True,
        "null": None,
        "empty": {},
        "with_russian": {
            "отправления": [{"id": 1, "name": "тест"}],
            "статистика": {"count": 5}
        }
    }

    selected_format = formats.get(format_type, formats["simple"])

    # Возвращаем как есть - FastAPI сам сериализует
    return selected_format

@router.get("/test-latin-only")
async def test_latin_only():
    """Тест только с латинскими символами"""
    return {
        "success": True,
        "message": "Test with latin only",
        "data": {
            "shipments": [],  # ← латиница вместо "отправления"
            "statistics": {   # ← латиница вместо "статистика"
                "total": 0,
                "processed": 0
            }
        }
    }


@router.get("/test-minimal")
async def test_minimal():
    """Минимальный тест - только латиница"""
    return {
        "result": "success",
        "data": {"count": 1},
        "test": True
    }


@router.get("/test-russian")
async def test_russian():
    """Тест с русскими символами"""
    return {
        "результат": "успех",
        "данные": {"количество": 1},
        "тест": True
    }


@router.get("/test-array")
async def test_array():
    """Тест с массивом"""
    return [1, 2, 3, 4, 5]


@router.get("/test-string")
async def test_string():
    """Тест только со строкой"""
    return "Just a string response"


@router.get("/test-number")
async def test_number():
    """Тест только с числом"""
    return 42


@router.get("/test-boolean")
async def test_boolean():
    """Тест только с boolean"""
    return True

@router.get("/test-simple-object")
async def test_simple_object():
    """Простейший объект для 1С"""
    return {
        "success": True,
        "message": "Тестовое сообщение",
        "data": {"items": []}
    }

@router.get("/status", summary="Статус сервиса")
async def get_service_status():
    """Простой статус"""
    from src.config import settings

    return {
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@router.get("/test", summary="Тест подключения")
async def test_connection():
    """Простой тест подключения"""
    return {
        "success": True,
        "message": "API доступен",
        "timestamp": datetime.now().isoformat()
    }
