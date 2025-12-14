"""
Мок-сервис для тестирования без реальных данных Ozon
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, AsyncGenerator
import logging

from src.models.schemas import EmbeddedPosting, ProductItem, FinancialData, AnalyticsData, DeliveryData

logger = logging.getLogger(__name__)


class MockTestService:
    """Мок-сервис для тестирования работы приложения без реального API Ozon"""

    def __init__(self, client_id: str = "test_client", api_key: str = "test_key"):
        self.client_id = client_id
        self.api_key = api_key
        self.errors = []
        self.warnings = []
        self.mock_data_available = True

    async def test_connection(self) -> Dict[str, Any]:
        """Тест подключения к мок-API"""
        return {
            "success": True,
            "message": "Mock connection successful",
            "auth_type": "Mock API",
            "endpoint_tested": "/mock/fbo/list",
            "has_data": True,
            "mock_mode": True
        }

    async def diagnose_api_access(self) -> Dict[str, Any]:
        """Диагностика доступности мок-эндпоинтов"""
        endpoints = [
            ("/mock/posting/fbo/list", "FBO List"),
            ("/mock/posting/fbo/get", "FBO Get Details"),
            ("/mock/analytics", "Analytics")
        ]

        results = {}
        for path, name in endpoints:
            results[name] = {
                "status": "success",
                "endpoint": path,
                "has_data": True,
                "response_keys": ["result", "postings", "products"],
                "mock_data": True
            }

        return {
            "client_id": self.client_id,
            "auth_type": "Mock API",
            "api_key_preview": f"{self.api_key[:10]}...",
            "mock_mode": True,
            "results": results,
            "summary": {
                "accessible_endpoints": [name for name in results.keys()],
                "blocked_endpoints": [],
                "note": "Все эндпоинты работают в мок-режиме"
            }
        }

    async def stream_postings(self, period_from: datetime, period_to: datetime) -> AsyncGenerator[
        List[EmbeddedPosting], None]:
        """Потоковая генерация мок-отправлений"""
        batch_size = 5
        total_batches = 3

        logger.info(f"Mock streaming from {period_from} to {period_to}")

        for batch_num in range(total_batches):
            try:
                postings = await self._generate_mock_batch(batch_num, period_from, period_to)

                logger.info(f"Generated mock batch {batch_num + 1}: {len(postings)} postings")
                yield postings

                # Имитация задержки API
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error generating mock batch: {e}")
                self.errors.append({
                    "type": "MOCK_GENERATION_ERROR",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                break

        logger.info(f"Mock streaming completed, total batches: {total_batches}")

    async def _generate_mock_batch(self, batch_num: int, period_from: datetime, period_to: datetime) -> List[
        EmbeddedPosting]:
        """Генерация батча мок-отправлений"""
        postings = []

        for i in range(5):  # 5 отправлений в батче
            posting_num = f"MOCK-{batch_num * 5 + i + 1:06d}"
            order_num = f"ORDER-{batch_num * 5 + i + 1:06d}"

            # Генерация товаров
            products = []
            for prod_idx in range(1, 4):  # 1-3 товара в отправлении
                price = 1000.0 * (prod_idx + batch_num)
                quantity = prod_idx
                total_price = price * quantity

                product = ProductItem(
                    line_number=prod_idx,
                    sku=100000 + batch_num * 10 + i * 3 + prod_idx,
                    name=f"Мок товар {prod_idx} (Партия {batch_num + 1})",
                    quantity=quantity,
                    price=price,
                    total=total_price,
                    posting_number=posting_num,
                    offer_id=f"OFFER-{batch_num * 10 + i * 3 + prod_idx}",
                    commission_percent=8.5,
                    commission_amount=total_price * 0.085,
                    payout=total_price * 0.915,
                    currency_code="RUB",
                    unit="шт",
                    vat_rate=20.0
                )
                products.append(product)

            # Финансовые данные
            total_products = sum(p.total for p in products)
            total_commission = sum(p.commission_amount or 0 for p in products)
            total_payout = sum(p.payout or 0 for p in products)

            finances = FinancialData(
                total_products=total_products,
                total_commission=total_commission,
                total_payout=total_payout,
                delivery_cost=300.0,
                refund_cost=0.0,
                currency="RUB"
            )

            # Аналитика
            analytics = AnalyticsData(
                warehouse_name=f"Мок-склад {batch_num + 1}",
                region="Московская область",
                city="Москва",
                delivery_type="fbo",
                warehouse_id=1000 + batch_num,
                tpl_provider="OZON LOGISTICS"
            )

            # Доставка
            delivery = DeliveryData(
                method="Курьерская доставка",
                tracking_number=f"TRACK-{posting_num}",
                warehouse=analytics.warehouse_name,
                delivery_date=(period_from + timedelta(days=batch_num + i)).isoformat() + "Z",
                address="г. Москва, ул. Моковая, д. 1",
                tpl_provider=analytics.tpl_provider
            )

            # Клиент
            customer = {
                "name": f"Иванов Иван Иванович {i}",
                "phone": f"+799900000{i:02d}",
                "email": f"client{i}@example.com",
                "address": delivery.address,
                "delivery_address": delivery.address
            }

            # Создаем отправление
            posting = EmbeddedPosting(
                posting_number=posting_num,
                order_number=order_num,
                status="delivered",
                status_ru="Доставлено",
                created_at=(period_from - timedelta(days=1)).isoformat() + "Z",
                in_process_at=(period_from - timedelta(hours=12)).isoformat() + "Z",
                товары=products,
                финансы=finances,
                аналитика=analytics,
                доставка=delivery,
                клиент=customer
            )

            postings.append(posting)

        return postings

    def get_errors(self) -> List[Dict[str, Any]]:
        """Получение ошибок"""
        return self.errors

    def get_warnings(self) -> List[Dict[str, Any]]:
        """Получение предупреждений"""
        return self.warnings

    def get_batch_count(self) -> int:
        """Получение количества батчей"""
        return 3

    def get_total_items(self) -> int:
        """Получение общего количества элементов"""
        return 15  # 3 батча × 5 отправлений

    async def close(self):
        """Закрытие сервиса"""
        logger.info("Mock service closed")
        pass