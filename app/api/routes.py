from fastapi import APIRouter, HTTPException
from ..models import PriceRequest, PriceResponse
from ..core.config import settings

router = APIRouter()

# Simple in-memory discount code table
DISCOUNT_CODES = {
    "WELCOME10": 0.10,
    "VIP20": 0.20,
    "SAVE5": 0.05,
}

@router.get("/healthz")
def healthz():
    return {"status": "ok", "env": settings.app_env}

@router.post("/v1/price", response_model=PriceResponse)
def calculate_price(payload: PriceRequest):
    vat_rate = payload.vat_rate if payload.vat_rate is not None else settings.vat_rate_default
    if not (0 <= vat_rate <= 1):
        raise HTTPException(status_code=400, detail="vat_rate must be between 0 and 1 (e.g., 0.2 for 20%)")

    discount_rate = 0.0
    applied_code = None
    if payload.discount_code:
        code = payload.discount_code.strip().upper()
        if code in DISCOUNT_CODES:
            discount_rate = DISCOUNT_CODES[code]
            applied_code = code
        else:
            raise HTTPException(status_code=400, detail="Invalid discount_code")

    vat_amount = payload.base_price * vat_rate
    price_with_vat = payload.base_price + vat_amount
    discount_amount = price_with_vat * discount_rate
    final_price = round(price_with_vat - discount_amount, 2)

    return PriceResponse(
        base_price=payload.base_price,
        vat_amount=round(vat_amount, 2),
        discount_amount=round(discount_amount, 2),
        final_price=final_price,
        applied_discount_code=applied_code,
    )
