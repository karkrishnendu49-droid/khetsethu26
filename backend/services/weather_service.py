import logging
from datetime import date
import httpx
from config.settings import OPEN_METEO_BASE_URL, HTTP_TIMEOUT, USER_AGENT
from utils.cache import weather_cache

logger = logging.getLogger('khetsetu.weather')

WMO = {0: 'Clear sky', 1: 'Mostly clear', 2: 'Partly cloudy', 3: 'Overcast', 45: 'Fog', 48: 'Fog',
       51: 'Light drizzle', 53: 'Drizzle', 55: 'Heavy drizzle', 61: 'Light rain', 63: 'Rain', 65: 'Heavy rain',
       71: 'Snow', 73: 'Snow', 75: 'Snow', 80: 'Rain showers', 81: 'Rain showers', 82: 'Heavy showers',
       95: 'Thunderstorm', 96: 'Thunderstorm', 99: 'Thunderstorm'}

def condition(code): return WMO.get(int(code or 0), 'Partly cloudy')

def demo_weather():
    return {'temperature': 31.4, 'rainfall': 2.4, 'humidity': 68, 'condition': 'Partly cloudy',
            'forecast': [
                {'date': date.today().isoformat(), 'max': 33, 'min': 26, 'rainfall': 1.2, 'condition': 'Partly cloudy'},
                {'date': date.today().isoformat(), 'max': 34, 'min': 27, 'rainfall': 0.0, 'condition': 'Mostly clear'},
                {'date': date.today().isoformat(), 'max': 32, 'min': 26, 'rainfall': 4.6, 'condition': 'Rain showers'}],
            'source': 'demo', 'demo': True}

async def get_weather(lat: float, lon: float):
    key = f'{lat:.2f},{lon:.2f}'
    cached = weather_cache.get(key)
    if cached: return cached
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers={'User-Agent': USER_AGENT}) as http:
            resp = await http.get(f'{OPEN_METEO_BASE_URL}/v1/forecast', params={
                'latitude': lat, 'longitude': lon, 'timezone': 'auto', 'forecast_days': 4,
                'current': 'temperature_2m,relative_humidity_2m,precipitation,weather_code',
                'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code'})
            resp.raise_for_status()
            data = resp.json()
            cur, daily = data['current'], data['daily']
            result = {
                'temperature': cur['temperature_2m'], 'rainfall': cur['precipitation'],
                'humidity': cur['relative_humidity_2m'], 'condition': condition(cur['weather_code']),
                'forecast': [{'date': daily['time'][i], 'max': daily['temperature_2m_max'][i],
                              'min': daily['temperature_2m_min'][i], 'rainfall': daily['precipitation_sum'][i],
                              'condition': condition(daily['weather_code'][i])} for i in range(1, min(4, len(daily['time'])))],
                'source': 'open-meteo', 'demo': False}
            weather_cache.set(key, result, 1800)
            return result
    except Exception as exc:
        logger.warning('Open-Meteo unavailable (%s), serving demo weather', exc)
        return demo_weather()
