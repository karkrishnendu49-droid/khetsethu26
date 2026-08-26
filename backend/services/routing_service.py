import logging
import httpx
from config.settings import OSRM_BASE_URL, HTTP_TIMEOUT, USER_AGENT
from utils.cache import route_cache
from utils.geo import haversine_km

logger = logging.getLogger('khetsetu.routing')

def estimate_cost(distance_km: float) -> int:
    return int(round((300 + 12.5 * distance_km) / 10) * 10)

async def get_route(from_lat: float, from_lon: float, to_lat: float, to_lon: float):
    key = f'{from_lat:.4f},{from_lon:.4f}|{to_lat:.4f},{to_lon:.4f}'
    cached = route_cache.get(key)
    if cached: return cached
    try:
        url = f'{OSRM_BASE_URL}/route/v1/driving/{from_lon},{from_lat};{to_lon},{to_lat}'
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers={'User-Agent': USER_AGENT}) as http:
            resp = await http.get(url, params={'overview': 'full', 'geometries': 'geojson'})
            resp.raise_for_status()
            data = resp.json()
            if data.get('code') == 'Ok' and data.get('routes'):
                route = data['routes'][0]
                distance_km = round(route['distance'] / 1000, 1)
                result = {
                    'distance_km': distance_km,
                    'duration_min': int(round(route['duration'] / 60)),
                    'transport_cost': estimate_cost(distance_km),
                    'geometry': [[lat, lon] for lon, lat in route['geometry']['coordinates']],
                    'source': 'osrm',
                }
                route_cache.set(key, result, 21600)
                return result
    except Exception as exc:
        logger.warning('OSRM unavailable (%s), using estimated route', exc)
    distance_km = round(haversine_km(from_lat, from_lon, to_lat, to_lon) * 1.3, 1)
    result = {
        'distance_km': distance_km,
        'duration_min': int(round(distance_km / 35 * 60)),
        'transport_cost': estimate_cost(distance_km),
        'geometry': [[from_lat, from_lon], [to_lat, to_lon]],
        'source': 'estimate',
    }
    route_cache.set(key, result, 1800)
    return result
