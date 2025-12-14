import asyncio
from typing import AsyncGenerator, List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import logging
import json
import aiohttp

from src.transformers.embedded_transformer import EmbeddedDataTransformer
from src.models.schemas import EmbeddedPosting
from src.utils.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


class HTTPError(Exception):
    """Кастомная ошибка для HTTP уровня"""

    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(f"HTTP {status}: {message}")


class OzonService:
    """Упрощенный сервис Ozon FBO"""

    def __init__(self, client_id: str, api_key: str):
        self.client_id = client_id
        self.api_key = api_key
        self.error_handler = ErrorHandler()
        self.transformer = EmbeddedDataTransformer()
        self.batch_count = 0
        self.total_items = 0
        self.session = None

        logger.info(f"OzonService инициализирован для client_id: {client_id[:10]}...")

    async def __aenter__(self):
        """Вход в контекстный менеджер"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекстного менеджера"""
        await self.close()


    async def start(self):
        """Инициализация сессии"""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                connector=aiohttp.TCPConnector(limit=10)
            )
            logger.debug("Сессия aiohttp создана")

    async def close(self):
        """Закрытие сессии"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
            logger.debug("Сессия aiohttp закрыта")

    async def _make_api_request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Упрощенный HTTP запрос"""
        # Задержка для rate limiting
        await asyncio.sleep(0.3)

        if not self.session or self.session.closed:
            await self.start()

        headers = {
            "Client-Id": self.client_id,
            "Api-Key": self.api_key,
            "Content-Type": "application/json"
        }

        try:
            async with self.session.request(
                    method=method,
                    url=f"https://api-seller.ozon.ru{path}",
                    headers=headers,
                    json=kwargs.get('json'),
                    timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:

                if resp.status != 200:
                    error_text = await resp.text()
                    logger.warning(f"API error {resp.status}: {error_text[:200]}")
                    raise HTTPError(resp.status, f"API returned {resp.status}")

                response = await resp.json()
                return response

        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            raise HTTPError(0, f"Network error: {str(e)}")
        except asyncio.TimeoutError:
            logger.error("Request timeout")
            raise HTTPError(0, "Request timeout")

    def _format_date_for_ozon(self, date_obj: datetime) -> str:
        """Форматирует дату для Ozon API"""
        return date_obj.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    async def _get_postings_batch(self, period_from: datetime, period_to: datetime, limit: int, offset: int) -> Dict[
        str, Any]:
        """Получение батча отправлений """
        try:
            since_str = self._format_date_for_ozon(period_from)
            to_str = self._format_date_for_ozon(period_to)

            params = {
                "dir": "ASC",
                "filter": {"since": since_str, "to": to_str},
                "limit": limit,
                "offset": offset,
                "translit": True,
                "with": {
                    "analytics_data": True,
                    "financial_data": True,
                    "barcodes": True
                }
            }

            logger.info(f"Requesting batch: offset={offset}, limit={limit}, from={since_str}, to={to_str}")

            response = await self._make_api_request(
                method="POST",
                path="/v2/posting/fbo/list",
                json=params
            )

            logger.debug(f"Response keys: {list(response.keys())}")

            # Вариант 1: Ошибка API
            if "error" in response:
                error_msg = response.get("error", "Unknown error")
                logger.error(f"Ozon API error: {error_msg}")
                return {"postings": [], "count": 0}

            # Вариант 2: Стандартная структура Ozon
            if "result" in response:
                result = response["result"]
                logger.debug(f"Result type: {type(result)}")

                if isinstance(result, dict):
                    # Ozon v2 API: result содержит postings
                    postings = result.get("postings", [])
                    count = result.get("count", len(postings))
                    logger.info(f"Got {len(postings)} postings (count: {count})")
                    return {"postings": postings, "count": count}
                elif isinstance(result, list):
                    # Ozon иногда возвращает список напрямую
                    logger.info(f"Result is direct list: {len(result)} items")
                    return {"postings": result, "count": len(result)}
                else:
                    logger.warning(f"Unexpected result type: {type(result)}")

            # Вариант 3: Проверяем верхний уровень
            if "postings" in response:
                postings = response.get("postings", [])
                count = response.get("count", len(postings))
                logger.info(f"Found postings at top level: {len(postings)}")
                return {"postings": postings, "count": count}

            # Вариант 4: Пустой или непонятный ответ
            logger.warning(f"No postings found. Full response structure: {list(response.keys())}")


            if logger.isEnabledFor(logging.DEBUG):
                import json
                logger.debug(f"Full response: {json.dumps(response, ensure_ascii=False, indent=2)[:500]}")


            return {"postings": [], "count": 0}

        except Exception as e:
            logger.error(f"Error getting batch: {e}", exc_info=True)
            return {"postings": [], "count": 0}

    async def _get_posting_details(self, posting_number: str) -> Optional[Dict[str, Any]]:
        """Получение деталей одного отправления"""
        if not posting_number:
            return None

        try:
            params = {
                "posting_number": posting_number,
                "with": {
                    "analytics_data": True,
                    "financial_data": True,
                    "barcodes": True,
                    "translit": True
                }
            }

            response = await self._make_api_request(
                method="POST",
                path="/v2/posting/fbo/get",
                json=params
            )

            return response.get("result")

        except Exception as e:
            logger.warning(f"Error getting details for {posting_number}: {e}")
            return None



    async def _process_batch(self, posting_batch: List[Dict[str, Any]]) -> List[EmbeddedPosting]:
        """Обработка батча - БЫСТРАЯ версия"""
        if not posting_batch:
            return []

        logger.info(f"Processing batch of {len(posting_batch)} postings...")

        embedded_postings = []
        processed_count = 0

        # Обрабатываем БОЛЬШИМИ пачками, но с задержками
        BATCH_SIZE = 10  # 10 отправлений за раз
        DELAY_BETWEEN_BATCHES = 0.5  # 0.5 сек между пачками

        for i in range(0, len(posting_batch), BATCH_SIZE):
            batch_chunk = posting_batch[i:i + BATCH_SIZE]

            # Создаем задачи для текущей пачки
            tasks = []
            for posting in batch_chunk:
                posting_number = posting.get("posting_number")
                if posting_number:
                    tasks.append(self._get_posting_details(str(posting_number)))

            if tasks:
                try:
                    # Выполняем пачку параллельно
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    for result in results:
                        processed_count += 1

                        #  прогресс каждые 50 отправлений
                        if processed_count % 50 == 0:
                            logger.info(f"Processed {processed_count}/{len(posting_batch)} postings")

                        if isinstance(result, Exception):
                            logger.debug(f"Task error: {result}")
                            continue

                        if result:
                            try:
                                transformed = await self.transformer.transform_single_posting(result)
                                if transformed:
                                    embedded_postings.append(transformed)
                            except Exception as e:
                                logger.debug(f"Transform error: {e}")
                                continue

                except Exception as e:
                    logger.error(f"Error processing batch chunk: {e}")

            # Задержка между пачками для rate limiting
            if i + BATCH_SIZE < len(posting_batch):
                await asyncio.sleep(DELAY_BETWEEN_BATCHES)

        logger.info(f"Batch processing complete: {len(embedded_postings)} embedded postings created")
        return embedded_postings

    async def stream_postings(self, period_from: datetime, period_to: datetime) -> AsyncGenerator[
        List[EmbeddedPosting], None]:
        """Передача данных в трансформер"""
        self.batch_count = 0
        self.total_items = 0

        await self.start()

        try:
            offset = 0
            limit = 1000

            while True:
                if offset > 0:
                    await asyncio.sleep(0.5)

                batch_result = await self._get_postings_batch(period_from, period_to, limit, offset)
                raw_postings = batch_result.get("postings", [])
                postings_count = batch_result.get("count", 0)

                logger.info(f"Batch {offset // limit + 1}: {len(raw_postings)} postings")

                if not raw_postings:
                    break

                # Обрабатываем постings
                embedded_batch = []
                for posting in raw_postings:
                    try:

                        transformed = await self.transformer.transform_single_posting(posting)
                        if transformed:
                            embedded_batch.append(transformed)
                    except Exception as e:

                        logger.debug(f"Transform error: {e}")
                        continue

                if embedded_batch:
                    self.batch_count += 1
                    self.total_items += len(embedded_batch)
                    logger.info(f"Successfully transformed: {len(embedded_batch)} postings")
                    yield embedded_batch
                else:
                    logger.warning(f"No postings transformed from {len(raw_postings)} raw postings")
                    # Для отладки выведем первый posting
                    if raw_postings and logger.isEnabledFor(logging.DEBUG):
                        import json
                        logger.debug(f"First raw posting structure: {json.dumps(raw_postings[0], indent=2)[:500]}")

                if len(raw_postings) < limit:
                    break

                offset += limit

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            raise
        finally:
            logger.info(f"Total: {self.total_items} postings in {self.batch_count} batches")

    def get_errors(self) -> List[Dict[str, Any]]:
        return self.error_handler.errors

    def get_warnings(self) -> List[Dict[str, Any]]:
        return self.error_handler.warnings