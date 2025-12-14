import json
from typing import Dict, Any, List
from datetime import datetime
import logging

from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class ResponseBuilder:
    """Сервис для формирования ответа 1С"""

    async def build_response(
            self,
            embedded_postings: List[Any],
            metadata: Dict[str, Any],
            total_items: int = 0,
            errors: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Формирует JSON-ответ совместимый с 1С ЧтениеJSON"""

        # 1. Преобразуем все данные в JSON-совместимые типы
        postings_list = self._convert_to_json_types(embedded_postings)

        # 2. Статистика
        statistics = self._calculate_statistics(embedded_postings)

        # 3. Обработка ошибок
        if errors is None:
            errors = {"errors": [], "warnings": []}

        # 4. Формируем финальный ответ
        response = {
            "success": True,  # boolean, не строка!
            "message": "Success",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "отправления": postings_list,
                "статистика": statistics
            },
            "metadata": {
                **self._clean_metadata(metadata),
                "обработано_отправлений": len(postings_list),  # int
                "всего_найдено": total_items  # int
            },
            "errors": self._clean_list(errors.get("errors", [])),
            "warnings": self._clean_list(errors.get("warnings", []))
        }

        # 5. Проверяем валидность JSON
        self._validate_json_compatibility(response)

        return response

    def _convert_to_json_types(self, data: Any) -> Any:
        """Рекурсивно преобразует данные в JSON-совместимые типы"""
        if isinstance(data, dict):
            # Обрабатываем словарь
            result = {}
            for key, value in data.items():
                # Обрабатываем специальные поля
                if key == "success":
                    # Убедимся, что success - boolean
                    if isinstance(value, str):
                        result[key] = value.lower() == "true"
                    else:
                        result[key] = bool(value)
                else:
                    result[key] = self._convert_to_json_types(value)
            return result

        elif isinstance(data, list):
            # Обрабатываем список
            return [self._convert_to_json_types(item) for item in data]

        elif hasattr(data, 'dict'):
            # Pydantic модель
            return self._convert_to_json_types(data.dict())

        elif isinstance(data, (int, float, bool, type(None))):

            return data

        elif isinstance(data, str):

            return data

        elif isinstance(data, datetime):

            return data.isoformat()

        else:

            try:
                return str(data)
            except:
                return None

    def _clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Очищает метаданные для JSON"""
        cleaned = {}
        for key, value in metadata.items():
            if isinstance(value, (int, float, bool, str, type(None))):
                cleaned[key] = value
            elif isinstance(value, dict):
                cleaned[key] = self._clean_metadata(value)
            elif isinstance(value, list):
                cleaned[key] = [str(item) for item in value]
            else:
                cleaned[key] = str(value)
        return cleaned

    def _clean_list(self, items: List[Any]) -> List[Dict[str, Any]]:
        """Очищает список ошибок/предупреждений"""
        result = []
        for item in items:
            if isinstance(item, dict):
                result.append(self._clean_metadata(item))
            else:
                result.append({"message": str(item)})
        return result

    def _validate_json_compatibility(self, data: Any):
        """Проверяет, что данные могут быть сериализованы в JSON"""
        try:
            json_str = json.dumps(data, ensure_ascii=False)
            # Пробуем десериализовать обратно
            json.loads(json_str)
            logger.debug("JSON compatibility check passed")
        except Exception as e:
            logger.error(f"JSON compatibility error: {e}")
            logger.debug(f"Problematic data: {data}")

    def _calculate_statistics(self, postings: List[Any]) -> Dict[str, Any]:
        """Рассчитывает статистику"""
        total_postings = len(postings)

        if total_postings == 0:
            return {
                "всего_отправлений": 0,
                "всего_товарных_позиций": 0,
                "сумма_товаров": 0,
                "сумма_выплат": 0,
                "сумма_комиссий": 0,
                "средняя_комиссия_процент": 0
            }

        total_products = 0
        total_payout = 0.0
        total_commission = 0.0
        total_products_value = 0.0

        for posting in postings:
            if hasattr(posting, 'товары'):
                # Pydantic модель
                total_products += len(posting.товары)
                total_payout += posting.финансы.total_payout
                total_commission += posting.финансы.total_commission
                total_products_value += posting.финансы.total_products
            elif isinstance(posting, dict):
                # Словарь
                total_products += len(posting.get('товары', []))
                finances = posting.get('финансы', {})
                total_payout += finances.get('total_payout', 0.0)
                total_commission += finances.get('total_commission', 0.0)
                total_products_value += finances.get('total_products', 0.0)

        avg_commission_percent = (
            (total_commission / total_products_value * 100)
            if total_products_value > 0 else 0
        )

        return {
            "всего_отправлений": int(total_postings),  # ← int
            "всего_товарных_позиций": int(total_products),  # ← int
            "сумма_товаров": float(round(total_products_value, 2)),  # ← float
            "сумма_выплат": float(round(total_payout, 2)),  # ← float
            "сумма_комиссий": float(round(total_commission, 2)),  # ← float
            "средняя_комиссия_процент": float(round(avg_commission_percent, 1))  # ← float
        }

    def create_http_response(self, response_data: Dict[str, Any], status_code: int = 200):
        """Создает HTTP-ответ с ПРАВИЛЬНОЙ кодировкой для 1С"""


        if not isinstance(response_data, dict):
            response_data = {"error": f"Invalid response type: {type(response_data)}"}

        # Создаем JSONResponse с UTF-8 кодировкой
        return JSONResponse(
            content=response_data,
            status_code=status_code,
            media_type="application/json; charset=utf-8",  # ← ВАЖНО!
            headers={
                "Content-Type": "application/json; charset=utf-8"  # ← И здесь тоже
            }
        )

