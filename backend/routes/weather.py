from fastapi import APIRouter
from services.weather_service import get_weather

router = APIRouter(prefix='/api')

@router.get('/weather')
async def weather(lat: float = 23.4710, lon: float = 88.5565):
    return await get_weather(lat, lon)
