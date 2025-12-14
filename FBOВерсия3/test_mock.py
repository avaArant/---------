# test_mock_service.py
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Добавляем путь к src в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fastapi.testclient import TestClient
from src.main import app
import json

client = TestClient(app)


def test_root_endpoint():
    """Тест корневого эндпоинта"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    print("✓ Корневой эндпоинт работает")
    print(f"  Сервис: {data.get('service')}")
    print(f"  Версия: {data.get('version')}")
    return True


def test_health_check():
    """Тест health check"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    print("✓ Health check работает")
    print(f"  Статус: {data.get('status')}")
    print(f"  Mock тесты: {data.get('dependencies', {}).get('mock_tests', 'unknown')}")
    return True


def test_mock_fbo_postings():
    """Тест основного эндпоинта с мок-данными"""
    headers = {
        "Client-Id": "test12345",
        "Api-Key": "test-api-key-1234567890",
        "Content-Type": "application/json"
    }

    payload = {
        "period_from": "2024-01-01T00:00:00Z",
        "period_to": "2024-01-02T00:00:00Z"
    }

    response = client.post("/api/v1/ozon/test/fbo-postings",
                           json=payload,
                           headers=headers)

    assert response.status_code == 200
    data = response.json()

    print("✓ Mock FBO эндпоинт работает")
    print(f"  Статус: {data.get('success', False)}")
    print(f"  Отправлений: {data.get('metadata', {}).get('обработано_отправлений', 0)}")

    # Проверяем структуру ответа
    assert "data" in data
    assert "отправления" in data["data"]
    assert "статистика" in data["data"]

    return True


def test_quick_test():
    """Тест быстрой проверки сервиса"""
    response = client.get("/api/v1/ozon/test/quick-test")
    assert response.status_code == 200
    data = response.json()

    print("✓ Quick test работает")
    print(f"  Сервис: {data.get('service')}")
    print(f"  Статус: {data.get('status')}")

    # Проверяем что есть команды для curl
    assert "test_curl_commands" in data
    return True


def test_check_all_systems():
    """Тест комплексной проверки"""
    response = client.get("/api/v1/ozon/test/check-all")
    assert response.status_code == 200
    data = response.json()

    print("✓ Комплексная проверка работает")
    print(f"  Общий статус: {data.get('overall_status')}")

    # Проверяем ключевые компоненты
    checks = data.get("checks", {})
    assert "app" in checks
    assert "redis" in checks
    assert "port" in checks

    return True


def test_cache_status():
    """Тест статуса кэша"""
    response = client.get("/cache/status")
    assert response.status_code == 200
    data = response.json()

    print("✓ Статус кэша работает")
    print(f"  Кэш включен: {data.get('enabled', False)}")
    return True


def test_mock_diagnose():
    """Тест диагностики в мок-режиме"""
    headers = {
        "Client-Id": "test12345",
        "Api-Key": "test-api-key-1234567890"
    }

    response = client.post("/api/v1/ozon/test/diagnose", headers=headers)
    assert response.status_code == 200
    data = response.json()

    print("✓ Mock диагностика работает")
    print(f"  Mock режим: {data.get('mock_mode', False)}")
    print(f"  Доступные эндпоинты: {len(data.get('summary', {}).get('accessible_endpoints', []))}")
    return True


def test_service_status():
    """Тест статуса сервиса"""
    response = client.get("/api/v1/ozon/status")
    assert response.status_code == 200
    data = response.json()

    print("✓ Статус сервиса работает")
    print(f"  Сервис: {data.get('service')}")
    print(f"  Версия: {data.get('version')}")
    return True


def test_api_test_endpoint():
    """Тест проверки доступности API эндпоинтов"""
    response = client.get("/api-test")
    assert response.status_code == 200
    data = response.json()

    print("✓ API test эндпоинт работает")
    print(f"  Тестовый роутер доступен: {data.get('test_router_available', False)}")
    return True


async def run_all_tests():
    """Запуск всех тестов"""
    print("=" * 60)
    print("ЗАПУСК МОК-ТЕСТОВ OZON FBO STREAMING API")
    print("=" * 60)

    tests = [
        ("Корневой эндпоинт", test_root_endpoint),
        ("Health check", test_health_check),
        ("Mock FBO отправления", test_mock_fbo_postings),
        ("Quick test", test_quick_test),
        ("Комплексная проверка", test_check_all_systems),
        ("Статус кэша", test_cache_status),
        ("Mock диагностика", test_mock_diagnose),
        ("Статус сервиса", test_service_status),
        ("API тест", test_api_test_endpoint),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\n▶ Тест: {test_name}")
            print("-" * 40)

            if asyncio.iscoroutinefunction(test_func):
                success = await test_func()
            else:
                success = test_func()

            if success:
                passed += 1
            else:
                failed += 1
                print(f"✗ Тест не прошел: {test_name}")

        except Exception as e:
            print(f"✗ Ошибка в тесте '{test_name}': {str(e)}")
            failed += 1

    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    print(f"✓ Успешно: {passed}")
    print(f"✗ Неудачно: {failed}")
    print(f"📊 Всего тестов: {passed + failed}")

    if failed == 0:
        print("\n🎉 Все тесты успешно пройдены!")
    else:
        print(f"\n⚠️ {failed} тестов не пройдено")

    return passed, failed


def generate_curl_commands():
    """Генерация curl команд для ручного тестирования"""
    print("\n" + "=" * 60)
    print("CURL КОМАНДЫ ДЛЯ ТЕСТИРОВАНИЯ")
    print("=" * 60)

    commands = [
        "# 1. Проверка статуса сервиса",
        "curl -X GET http://localhost:8001/",
        "",
        "# 2. Health check",
        "curl -X GET http://localhost:8001/health",
        "",
        "# 3. Комплексная проверка (требует тестового роутера)",
        "curl -X GET http://localhost:8001/api/v1/ozon/test/check-all",
        "",
        "# 4. Быстрый тест сервиса",
        "curl -X GET http://localhost:8001/api/v1/ozon/test/quick-test",
        "",
        "# 5. Тест с мок-данными (работает без реального API Ozon)",
        'curl -X POST http://localhost:8001/api/v1/ozon/test/fbo-postings \\',
        '  -H "Client-Id: test12345" \\',
        '  -H "Api-Key: test-api-key-1234567890" \\',
        '  -H "Content-Type: application/json" \\',
        '  -d \'{"period_from": "2024-01-01T00:00:00Z", "period_to": "2024-01-02T00:00:00Z"}\'',
        "",
        "# 6. Mock диагностика",
        'curl -X POST http://localhost:8001/api/v1/ozon/test/diagnose \\',
        '  -H "Client-Id: test12345" \\',
        '  -H "Api-Key: test-api-key-1234567890"',
        "",
        "# 7. Статус кэша",
        "curl -X GET http://localhost:8001/cache/status",
    ]

    for cmd in commands:
        print(cmd)


def main():
    """Основная функция запуска тестов"""
    try:
        # Запускаем асинхронные тесты
        passed, failed = asyncio.run(run_all_tests())

        if passed > 0:
            generate_curl_commands()

            print("\n" + "=" * 60)
            print("ИНСТРУКЦИЯ ПО ЗАПУСКУ СЕРВИСА")
            print("=" * 60)
            print("1. Запустите сервис командой:")
            print("   python -m src.main")
            print("\n2. В отдельном терминале запустите тесты:")
            print("   python test_mock_service.py")
            print("\n3. Или используйте curl команды выше для ручного тестирования")

        return 0 if failed == 0 else 1

    except Exception as e:
        print(f"\n❌ Критическая ошибка при запуске тестов: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)