import asyncio
from fastapi.testclient import TestClient
from src.main import app
from datetime import datetime, timedelta
import time

client = TestClient(app)


def test_complete_workflow():
    """Полный тест рабочего процесса с уменьшенным объемом данных"""
    print("\n" + "=" * 60)
    print("Testing FBO Postings Endpoint - COMPLETE WORKFLOW")
    print("=" * 60)

    # Тестовые данные (ЗАПОЛНИТЕ СВОИМИ ДАННЫМИ!)
    CLIENT_ID = "2115535"  # Ваш Client-Id
    API_KEY = "5ffc-943c9bb875a3"  # Ваш Api-Key

    # Уменьшенный период для теста - 6 ЧАСОВ вместо 1 дня
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=6)

    request_data = {
        "period_from": start_date.isoformat(),
        "period_to": end_date.isoformat()
    }

    valid_headers = {
        "Client-Id": CLIENT_ID,
        "Api-Key": API_KEY
    }

    print(f"📋 Test Configuration:")
    print(f"  • Client-Id: {CLIENT_ID}")
    print(f"  • Api-Key preview: {API_KEY[:10]}...")
    print(f"  • Period: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"  • Duration: 6 hours (reduced for testing)")
    print()

    # ============================================================
    # 1. ТЕСТ АВТОРИЗАЦИИ (без заголовков)
    # ============================================================
    print("🔐 Test 1: Authentication (missing headers)...")
    try:
        response = client.post(
            "/api/v1/ozon/fbo-postings",
            json=request_data,
            headers={},  # Пустые заголовки
            timeout=5.0
        )

        if response.status_code == 401:
            print("  ✅ PASS: Returns 401 without auth headers")
            error_detail = response.json().get("detail", "")
            print(f"     Error message: {error_detail}")
        else:
            print(f"  ❌ FAIL: Expected 401, got {response.status_code}")
            print(f"     Response: {response.text[:200]}")

    except Exception as e:
        print(f"  ⚠️  ERROR: {type(e).__name__}: {e}")

    # ============================================================
    # 2. ТЕСТ ВАЛИДАЦИИ ПЕРИОДА (неверный формат даты)
    # ============================================================
    print("\n📅 Test 2: Date validation (invalid format)...")
    try:
        invalid_data = {
            "period_from": "invalid-date-format",
            "period_to": "another-invalid"
        }

        response = client.post(
            "/api/v1/ozon/fbo-postings",
            json=invalid_data,
            headers=valid_headers,
            timeout=5.0
        )

        if response.status_code == 400:
            print("  ✅ PASS: Returns 400 for invalid date format")
            error_detail = response.json().get("detail", "")
            print(f"     Error message: {error_detail}")
        else:
            print(f"  ❌ FAIL: Expected 400, got {response.status_code}")
            print(f"     Response: {response.text[:200]}")

    except Exception as e:
        print(f"  ⚠️  ERROR: {type(e).__name__}: {e}")

    # ============================================================
    # 3. ТЕСТ ОБРАТНОГО ПЕРИОДА (начало позже окончания)
    # ============================================================
    print("\n🔄 Test 3: Date validation (reversed period)...")
    try:
        reversed_data = {
            "period_from": end_date.isoformat(),  # Начало позже
            "period_to": start_date.isoformat()  # Окончание раньше
        }

        response = client.post(
            "/api/v1/ozon/fbo-postings",
            json=reversed_data,
            headers=valid_headers,
            timeout=5.0
        )

        if response.status_code == 400:
            print("  ✅ PASS: Returns 400 for reversed period")
            error_detail = response.json().get("detail", "")
            print(f"     Error message: {error_detail}")
        else:
            print(f"  ❌ FAIL: Expected 400, got {response.status_code}")
            print(f"     Response: {response.text[:200]}")

    except Exception as e:
        print(f"  ⚠️  ERROR: {type(e).__name__}: {e}")

    # ============================================================
    # 4. ОСНОВНОЙ ТЕСТ (успешный запрос)
    # ============================================================
    print("\n🚀 Test 4: Main endpoint test (valid request)...")
    print("  Note: This may take 30-60 seconds depending on data volume")

    start_time = time.time()

    try:
        # Увеличенный таймаут для длительной обработки
        response = client.post(
            "/api/v1/ozon/fbo-postings",
            json=request_data,
            headers=valid_headers,
            timeout=120.0  # 120 секунд таймаут!
        )

        elapsed_time = time.time() - start_time
        print(f"  ⏱️  Request took: {elapsed_time:.2f} seconds")

        if response.status_code == 200:
            print("  ✅ SUCCESS: Got 200 response")

            result = response.json()

            # Проверка структуры ответа
            print(f"  📊 Response structure:")
            print(f"     • success: {result.get('success')}")
            print(f"     • message: {result.get('message')}")
            print(f"     • timestamp: {result.get('timestamp')}")

            # Проверка данных
            if "data" in result:
                data = result["data"]
                postings_count = len(data.get("отправления", []))
                print(f"     • postings count: {postings_count}")

                if postings_count > 0:
                    print(f"  📦 Data details (first posting):")
                    first_posting = data["отправления"][0]
                    print(f"     • posting_number: {first_posting.get('posting_number')}")
                    print(f"     • status: {first_posting.get('status')}")
                    print(f"     • товары count: {len(first_posting.get('товары', []))}")
                else:
                    print(f"  ℹ️  No postings found for the selected period")

            # Проверка ошибок и предупреждений
            errors_count = len(result.get("errors", []))
            warnings_count = len(result.get("warnings", []))

            if errors_count > 0:
                print(f"  ⚠️  Found {errors_count} errors:")
                for i, error in enumerate(result["errors"][:3]):  # Покажем только первые 3
                    print(f"     {i + 1}. {error.get('code', 'No code')}: {error.get('message', 'No message')}")
                if errors_count > 3:
                    print(f"     ... and {errors_count - 3} more errors")

            if warnings_count > 0:
                print(f"  ⚠️  Found {warnings_count} warnings")

            # Проверка метаданных
            metadata = result.get("metadata", {})
            print(f"  📋 Metadata:")
            print(f"     • client_id: {metadata.get('client_id')}")
            print(f"     • обработано_отправлений: {metadata.get('обработано_отправлений')}")
            print(f"     • всего_найдено: {metadata.get('всего_найдено')}")

        elif response.status_code == 401:
            print("  ❌ FAIL: Authentication failed (check API key)")
            error_detail = response.json().get("detail", "")
            print(f"     Error: {error_detail}")

        elif response.status_code == 429:
            print("  ⚠️  WARNING: Rate limited by Ozon API")
            print("     Try again in a few minutes or reduce request frequency")

        else:
            print(f"  ❌ FAIL: Unexpected status code {response.status_code}")
            try:
                error_data = response.json()
                print(f"     Error: {error_data}")
            except:
                print(f"     Raw response (first 500 chars):")
                print(f"     {response.text[:500]}...")

    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"  ❌ ERROR after {elapsed_time:.2f} seconds: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    # ============================================================
    # 5. ДОПОЛНИТЕЛЬНЫЕ ТЕСТЫ ЭНДПОИНТОВ
    # ============================================================
    print("\n🧪 Test 5: Additional endpoints...")

    # Тест диагностики
    print("  Testing /diagnose endpoint...")
    try:
        response = client.post(
            "/api/v1/ozon/diagnose",
            headers=valid_headers,
            timeout=10.0
        )

        if response.status_code == 200:
            diagnose_data = response.json()
            print(f"    ✅ Diagnose works")
            print(f"       • client_id: {diagnose_data.get('client_id')}")
            print(f"       • auth_type: {diagnose_data.get('auth_type')}")
        else:
            print(f"    ❌ Diagnose failed: {response.status_code}")

    except Exception as e:
        print(f"    ⚠️  Diagnose error: {e}")

    # Тест статуса
    print("  Testing /status endpoint...")
    try:
        response = client.get(
            "/api/v1/ozon/status",
            timeout=5.0
        )

        if response.status_code == 200:
            status_data = response.json()
            print(f"    ✅ Status works")
            print(f"       • service: {status_data.get('service')}")
            print(f"       • version: {status_data.get('version')}")
        else:
            print(f"    ❌ Status failed: {response.status_code}")

    except Exception as e:
        print(f"    ⚠️  Status error: {e}")

    print("\n" + "=" * 60)
    print("✅ TEST COMPLETED")
    print("=" * 60)


def test_small_period():
    """Тест с ОЧЕНЬ маленьким периодом для быстрой проверки"""
    print("\n" + "=" * 60)
    print("Testing with VERY SMALL period (30 minutes)")
    print("=" * 60)

    CLIENT_ID = "2115535"
    API_KEY = "ваш_api_key_здесь"

    # ОЧЕНЬ маленький период - 30 минут
    end_date = datetime.now()
    start_date = end_date - timedelta(minutes=30)

    request_data = {
        "period_from": start_date.isoformat(),
        "period_to": end_date.isoformat()
    }

    headers = {
        "Client-Id": CLIENT_ID,
        "Api-Key": API_KEY
    }

    print(f"Period: {start_date.strftime('%H:%M')} to {end_date.strftime('%H:%M')} (30 minutes)")
    print("This should complete very quickly...")

    try:
        response = client.post(
            "/api/v1/ozon/fbo-postings",
            json=request_data,
            headers=headers,
            timeout=30.0
        )

        print(f"\nResponse status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            postings_count = len(data.get('data', {}).get('отправления', []))
            print(f"✅ Got {postings_count} postings in 30 minute period")

            if postings_count == 0:
                print("ℹ️  No postings found - try a longer period")
            else:
                # Быстрая проверка структуры
                first = data['data']['отправления'][0]
                print(f"Sample posting: {first.get('posting_number')} - {first.get('status_ru')}")

        else:
            print(f"Response: {response.text[:300]}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Запуск тестов в порядке возрастания сложности

    print("Starting FBO API Tests...")
    print("=" * 60)

    # 1. Сначала быстрый тест с очень маленьким периодом
    test_small_period()

    # 2. Затем полный тест (раскомментируйте когда будете готовы)
    # test_complete_workflow()

    print("\n" + "=" * 60)
    print("🎉 All tests completed!")
    print("=" * 60)