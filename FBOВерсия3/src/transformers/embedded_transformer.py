# src/transformers/embedded_transformer.py
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.models.schemas import EmbeddedPosting, ProductItem, FinancialData, AnalyticsData, DeliveryData

logger = logging.getLogger(__name__)


class EmbeddedDataTransformer:

    async def transform_single_posting(self, posting_data: Dict[str, Any]) -> Optional[EmbeddedPosting]:
        """Преобразование данных отправления """

        # Если данные пришли обернутыми в "result"
        if "result" in posting_data:
            posting_data = posting_data["result"]

        if not posting_data:
            logger.debug("Empty posting_data")
            return None

        # Получаем номер отправления ЛЮБЫМ способом
        posting_number = None

        # Пробуем разные возможные ключи
        possible_keys = ["posting_number", "postingNumber", "posting"]
        for key in possible_keys:
            if key in posting_data:
                posting_number = str(posting_data[key])
                break

        if not posting_number:
            logger.debug(f"No posting number found. Keys: {list(posting_data.keys())}")
            return None

        logger.debug(f"Transforming posting: {posting_number}")

        try:
            # Создаем базовую структуру
            embedded_posting = EmbeddedPosting(
                posting_number=posting_number,
                order_number=str(posting_data.get("order_id", "")) if posting_data.get("order_id") else None,
                status=posting_data.get("status", ""),
                status_ru=self._translate_status(posting_data.get("status", "")),
                created_at=self._to_iso_string(posting_data.get("created_at")),
                in_process_at=self._to_iso_string(posting_data.get("in_process_at")),
                товары=self._extract_product_items_simple(posting_data),
                финансы=self._extract_financial_data_simple(posting_data),
                аналитика=self._extract_analytics_data_simple(posting_data),
                доставка=self._extract_delivery_data_simple(posting_data),
                клиент=self._extract_customer_data_simple(posting_data)
            )

            logger.debug(f"Successfully created EmbeddedPosting for {posting_number}")
            return embedded_posting

        except Exception as e:
            logger.error(f"Failed to create EmbeddedPosting for {posting_number}: {e}")
            logger.debug(f"Posting data keys: {list(posting_data.keys())}")
            return None

    def _extract_product_items_simple(self, posting_data: Dict[str, Any]) -> List[ProductItem]:
        """Упрощенное извлечение товаров"""
        product_items = []
        products = posting_data.get("products", [])

        posting_number = str(posting_data.get("posting_number", ""))

        for idx, product in enumerate(products, 1):
            try:
                quantity = product.get("quantity", 0)
                if quantity <= 0:
                    continue

                price = self._safe_float(product.get("price", "0"))
                total = price * quantity

                product_item = ProductItem(
                    line_number=idx,
                    sku=int(product.get("sku", 0)) if product.get("sku") else 0,
                    name=product.get("name", f"Товар {idx}"),
                    quantity=quantity,
                    price=price,
                    total=total,
                    posting_number=posting_number,
                    offer_id=product.get("offer_id"),
                    currency_code=product.get("currency_code", "RUB")
                )
                product_items.append(product_item)

            except Exception as e:
                logger.debug(f"Error extracting product: {e}")
                continue

        return product_items

    def _extract_financial_data_simple(self, posting_data: Dict[str, Any]) -> FinancialData:
        """Упрощенное извлечение финансов"""
        financial_data = FinancialData()

        try:
            # Считаем из продуктов
            products = posting_data.get("products", [])
            for product in products:
                quantity = product.get("quantity", 0)
                price = self._safe_float(product.get("price", "0"))
                financial_data.total_products += price * quantity

            # Предполагаем выплату = 90% от стоимости товаров
            financial_data.total_payout = financial_data.total_products * 0.9
            financial_data.total_commission = financial_data.total_products * 0.1

        except Exception as e:
            logger.debug(f"Error extracting financial data: {e}")

        return financial_data

    def _translate_status(self, status: str) -> str:
        """Перевод статуса"""
        status_map = {
            "awaiting_registration": "Ожидает регистрации",
            "acceptance_in_progress": "Приемка в процессе",
            "awaiting_approve": "Ожидает подтверждения",
            "awaiting_packaging": "Ожидает упаковки",
            "awaiting_deliver": "Ожидает отгрузки",
            "delivering": "Доставляется",
            "driver_pickup": "Водитель забрал",
            "delivered": "Доставлено",
            "cancelled": "Отменено",
            "arbitration": "Арбитраж"
        }
        return status_map.get(status, status)

    def _extract_customer_data_simple(self, posting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Упрощенное извлечение данных клиента"""
        customer = posting_data.get("customer", {})
        addressee = posting_data.get("addressee", {})

        return {
            "name": customer.get("name") or addressee.get("name"),
            "phone": customer.get("phone") or addressee.get("phone"),
            "email": customer.get("email"),
            "address": customer.get("address", ""),
            "delivery_address": addressee.get("address", "")
        }

    def _extract_delivery_data_simple(self, posting_data: Dict[str, Any]) -> DeliveryData:
        """Упрощенное извлечение данных доставки"""
        delivery_method = posting_data.get("delivery_method", {})
        addressee = posting_data.get("addressee", {})

        return DeliveryData(
            method=delivery_method.get("name"),
            tracking_number=posting_data.get("tracking_number"),
            warehouse=posting_data.get("warehouse", {}).get("name"),
            delivery_date=self._to_iso_string(posting_data.get("delivery_date")),
            address=addressee.get("address", ""),
            tpl_provider=delivery_method.get("tpl_provider")
        )

    def _extract_analytics_data_simple(self, posting_data: Dict[str, Any]) -> AnalyticsData:
        """Упрощенное извлечение аналитики"""
        analytics = posting_data.get("analytics_data", {})

        return AnalyticsData(
            warehouse_name=analytics.get("warehouse_name"),
            region=analytics.get("region"),
            city=analytics.get("city"),
            delivery_type=analytics.get("delivery_type"),
            warehouse_id=analytics.get("warehouse_id"),
            tpl_provider=analytics.get("tpl_provider")
        )

    def _to_iso_string(self, date_value: Any) -> Optional[str]:
        """Преобразование даты"""
        if not date_value:
            return None
        try:
            if isinstance(date_value, str):
                return date_value
            elif isinstance(date_value, datetime):
                return date_value.isoformat()
            else:
                return str(date_value)
        except Exception:
            return None

    def _safe_float(self, value: Any) -> float:
        """Безопасное преобразование в float"""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str):
                cleaned = value.strip().replace(' ', '').replace(',', '.')
                return float(cleaned) if cleaned else 0.0
            else:
                return 0.0
        except (ValueError, TypeError):
            return 0.0