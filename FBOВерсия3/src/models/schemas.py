from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class ProductItem(BaseModel):
    """Товарная позиция"""
    line_number: int
    sku: int
    name: str
    quantity: int
    price: float
    total: float
    unit: str = "шт"
    vat_rate: float = 20.0
    posting_number: str
    offer_id: Optional[str] = None
    commission_percent: Optional[float] = None
    commission_amount: Optional[float] = None
    payout: Optional[float] = None
    currency_code: str = "RUB"

    @validator('price', 'total', 'commission_percent', 'commission_amount', 'payout', pre=True)
    def validate_floats(cls, v):
        if v is None:
            return v
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0


class FinancialData(BaseModel):
    """Финансовые данные отправления"""
    total_products: float = 0.0
    total_commission: float = 0.0
    total_payout: float = 0.0
    delivery_cost: float = 0.0
    refund_cost: float = 0.0
    currency: str = "RUB"


class AnalyticsData(BaseModel):
    """Аналитические данные"""
    warehouse_name: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    delivery_type: Optional[str] = None
    warehouse_id: Optional[int] = None
    tpl_provider: Optional[str] = None


class DeliveryData(BaseModel):
    """Данные доставки"""
    method: Optional[str] = None
    tracking_number: Optional[str] = None
    warehouse: Optional[str] = None
    delivery_date: Optional[str] = None
    address: Optional[str] = None
    tpl_provider: Optional[str] = None


class EmbeddedPosting(BaseModel):
    """Вложенная структура отправления для 1С"""
    posting_number: str
    order_number: Optional[str] = None
    status: str
    status_ru: str
    created_at: str
    in_process_at: Optional[str] = None
    товары: List[ProductItem]
    финансы: FinancialData
    аналитика: AnalyticsData
    доставка: DeliveryData
    клиент: Dict[str, Any] = {}

    # Простая конфигурация - jsonable_encoder сделает всё остальное
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FBORequest(BaseModel):
    """Основной запрос от 1С"""
    period_from: str = Field(..., description="Начало периода в формате ISO")
    period_to: str = Field(..., description="Конец периода в формате ISO")



