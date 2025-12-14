from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Обработчик ошибок"""

    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.timeout_errors: List[Dict[str, Any]] = []
        self.retry_counts: Dict[str, int] = {}

    def add_error(self, error_type: str, message: str, details: Any = None):
        """Добавление ошибки"""
        error = {
            "type": error_type,
            "message": message,
            "details": details,
            "timestamp": self._get_timestamp(),
            "retryable": self._is_retryable(error_type)
        }
        self.errors.append(error)
        logger.error(f"Error: {error_type} - {message}")

    def add_warning(self, warning_type: str, message: str, details: Any = None):
        """Добавление предупреждения"""
        warning = {
            "type": warning_type,
            "message": message,
            "details": details,
            "timestamp": self._get_timestamp()
        }
        self.warnings.append(warning)
        logger.warning(f"Warning: {warning_type} - {message}")

    def add_timeout_error(self, operation: str, duration: float, retry_count: int = 0):
        """Добавление ошибки таймаута"""
        timeout_error = {
            "operation": operation,
            "duration_seconds": duration,
            "retry_count": retry_count,
            "timestamp": self._get_timestamp()
        }
        self.timeout_errors.append(timeout_error)
        logger.warning(f"Timeout in {operation}: {duration}s, retry {retry_count}")

    def should_retry(self, error_key: str, max_retries: int = 3) -> bool:
        """Проверка возможности повторной попытки"""
        current_retries = self.retry_counts.get(error_key, 0)
        if current_retries < max_retries:
            self.retry_counts[error_key] = current_retries + 1
            return True
        return False

    def reset_retry_count(self, error_key: str):
        """Сброс счетчика повторных попыток"""
        self.retry_counts.pop(error_key, None)

    def get_all_errors(self) -> Dict[str, List[Dict[str, Any]]]:
        """Получение всех ошибок и предупреждений"""
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "timeout_errors": self.timeout_errors
        }

    def has_errors(self) -> bool:
        """Проверка наличия ошибок"""
        return len(self.errors) > 0

    def has_timeout_errors(self) -> bool:
        """Проверка наличия ошибок таймаута"""
        return len(self.timeout_errors) > 0

    def clear(self):
        """Очистка ошибок"""
        self.errors.clear()
        self.warnings.clear()
        self.timeout_errors.clear()
        self.retry_counts.clear()

    def _is_retryable(self, error_type: str) -> bool:
        """Определение, можно ли повторить операцию при данной ошибке"""
        retryable_errors = {
            "NETWORK_ERROR",
            "TIMEOUT_ERROR",
            "API_RATE_LIMIT",
            "CONNECTION_RESET",
            "SERVER_ERROR_5XX"
        }
        return error_type in retryable_errors

    def _get_timestamp(self) -> str:
        return datetime.now().isoformat()