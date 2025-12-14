import logging
from typing import Optional
from src.services.ozon_service import OzonService

logger = logging.getLogger(__name__)


class OzonServiceFactory:
    """Упрощенная фабрика сервисов"""

    @staticmethod
    def create_service(
            client_id: str,
            api_key: str,
            request_id: Optional[str] = None
    ) -> OzonService:
        """
        Создает сервис для запроса
        """
        logger.info(f"Creating OzonService for client_id: {client_id[:10]}...")

        # Создаем сервис
        service = OzonService(client_id=client_id, api_key=api_key)

        return service