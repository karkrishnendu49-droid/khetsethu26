from typing import Optional
from fastapi import APIRouter
from services.market_price_service import get_prices

router = APIRouter(prefix='/api')

@router.get('/market-prices')
async def market_prices(crop: Optional[str] = None, location: Optional[str] = None, date: Optional[str] = None):
    return await get_prices(crop, location, date)
