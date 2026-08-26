import time
import httpx
from config.settings import OSRM_BASE_URL, OPEN_METEO_BASE_URL, HTTP_TIMEOUT, USER_AGENT, MAP_API_KEY, WEATHER_API_KEY, MARKET_API_KEY
from services.routing_service import get_route
from services.weather_service import get_weather
from services.market_price_service import get_prices
from utils.geo import NADIA, KOLKATA

async def _reachable(url, params=None):
    try:
        async with httpx.AsyncClient(timeout=4, headers={'User-Agent': USER_AGENT}) as http:
            resp = await http.get(url, params=params)
            return resp.status_code < 500
    except Exception:
        return False

async def integration_status():
    maps_ok = await _reachable(f'{OSRM_BASE_URL}/route/v1/driving/88.5565,23.4710;88.3639,22.5726', {'overview': 'false'})
    weather_ok = await _reachable(f'{OPEN_METEO_BASE_URL}/v1/forecast', {'latitude': 23.47, 'longitude': 88.55, 'current': 'temperature_2m'})
    return [
        {'service': 'maps', 'label': 'Maps API', 'status': 'connected' if maps_ok else 'error',
         'detail': 'OpenStreetMap tiles + OSRM routing (free tier, no key required).' if maps_ok else 'Routing provider unreachable — falling back to estimated routes.',
         'key_configured': bool(MAP_API_KEY)},
        {'service': 'weather', 'label': 'Weather API', 'status': 'connected' if weather_ok else 'demo',
         'detail': 'Open-Meteo live forecast (free tier, no key required).' if weather_ok else 'Weather provider unreachable — serving clearly labelled demo weather data.',
         'key_configured': bool(WEATHER_API_KEY)},
        {'service': 'market', 'label': 'Market Price API', 'status': 'demo',
         'detail': 'Seeded prototype mandi data. Connect a verified government/agri API via MARKET_API_KEY without frontend changes.',
         'key_configured': bool(MARKET_API_KEY)},
        {'service': 'geolocation', 'label': 'Geolocation', 'status': 'connected',
         'detail': 'Browser geolocation, requested on the client with explicit user permission.',
         'key_configured': True},
    ]

async def test_service(service: str):
    start = time.time()
    if service == 'maps':
        route = await get_route(NADIA[0], NADIA[1], KOLKATA[0], KOLKATA[1])
        status = 'success' if route['source'] == 'osrm' else 'demo'
        detail = f"Nadia → Kolkata: {route['distance_km']} km, {route['duration_min']} min, ₹{route['transport_cost']} ({route['source']})"
    elif service == 'weather':
        weather = await get_weather(NADIA[0], NADIA[1])
        status = 'demo' if weather['demo'] else 'success'
        detail = f"Nadia: {weather['temperature']}°C, {weather['condition']}, humidity {weather['humidity']}% ({weather['source']})"
    elif service == 'market':
        prices = await get_prices()
        status = 'demo'
        detail = f"{len(prices['rows'])} seeded mandi rows returned (Demo / Prototype Data)"
    else:
        return {'service': service, 'result': 'failed', 'detail': 'Unknown service.', 'latency_ms': 0}
    return {'service': service, 'result': status, 'detail': detail, 'latency_ms': int((time.time() - start) * 1000)}
