import asyncio
import json
import logging
from typing import Dict, Any, Optional
import aiohttp

logger = logging.getLogger(__name__)


class HTTPError(Exception):
    """Кастомная ошибка для HTTP уровня"""

    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(f"HTTP {status}: {message}")


class HTTPClient:
    """Отдельный HTTP клиент только для сетевых операций"""

    def __init__(self, base_url: str = "https://api-seller.ozon.ru"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Вход в контекстный менеджер"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            connector=aiohttp.TCPConnector(
                limit=50,
                limit_per_host=10,
                ttl_dns_cache=300,
                enable_cleanup_closed=True  # Автоочистка
            )
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекстного менеджера"""
        if self.session and not self.session.closed:
            await self.session.close()
        self.session = None

    async def request(
            self,
            method: str,
            path: str,
            headers: dict,
            json_data: dict = None,
            max_retries: int = 3
    ) -> Dict[str, Any]:
        """Только HTTP логика - без бизнес-логики Ozon API"""
        if not self.session:
            raise RuntimeError("Используйте HTTPClient как контекстный менеджер")

        for attempt in range(max_retries):
            try:
                async with self.session.request(
                        method=method,
                        url=f"{self.base_url}{path}",
                        headers=headers,
                        json=json_data,
                        timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:

                    response_text = await resp.text()

                    if not response_text:
                        if resp.status >= 400:
                            raise HTTPError(resp.status, "Empty response")
                        return {}

                    try:
                        response = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        if resp.status >= 400:
                            raise HTTPError(resp.status, f"Invalid JSON: {str(e)}")
                        raise ValueError(f"Response is not valid JSON: {str(e)}")

                    if resp.status >= 400:
                        error_msg = response.get('message') or response.get('error') or 'Unknown error'

                        if resp.status == 429:  # Rate limiting
                            wait_time = 2 ** (attempt + 1)
                            logger.warning(f"Rate limit hit, waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise HTTPError(resp.status, str(error_msg))

                    return response

            except aiohttp.ClientError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Network error, retry {attempt + 1}/{max_retries}: {str(e)}")
                    await asyncio.sleep(wait_time)
                    continue
                raise HTTPError(0, f"Network error after {max_retries} retries: {str(e)}")

            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Timeout, retry {attempt + 1}/{max_retries}")
                    await asyncio.sleep(wait_time)
                    continue
                raise HTTPError(0, f"Timeout after {max_retries} retries")

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Unexpected error, retry {attempt + 1}/{max_retries}: {str(e)}")
                    await asyncio.sleep(wait_time)
                    continue
                raise HTTPError(0, f"Unexpected error after {max_retries} retries: {str(e)}")

        raise HTTPError(0, f"Failed after {max_retries} attempts")