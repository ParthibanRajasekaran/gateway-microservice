from pydantic import BaseModel, Field
from typing import Optional

class PriceRequest(BaseModel):
    base_price: float = Field(..., gt=0, description="Base price before VAT and discounts")
    vat_rate: Optional[float] = Field(None, ge=0, le=1, description="VAT rate as a fraction, e.g., 0.2 for 20%")
    discount_code: Optional[str] = Field(None, description="Optional discount code")

class PriceResponse(BaseModel):
    base_price: float
    vat_amount: float
    discount_amount: float
    final_price: float
    applied_discount_code: Optional[str] = None
