import logging
import httpx
from config.settings import NOMINATIM_BASE_URL, HTTP_TIMEOUT, USER_AGENT
from utils.cache import geocode_cache
from utils.geo import gazetteer_lookup

logger = logging.getLogger('khetsetu.geocoding')

async def geocode(query: str):
    key = (query or '').strip().lower()
    if not key:
        return {'lat': 22.9868, 'lon': 87.8550, 'display_name': 'West Bengal, India', 'source': 'fallback'}
    cached = geocode_cache.get(key)
    if cached: return cached
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers={'User-Agent': USER_AGENT}) as http:
            resp = await http.get(f'{NOMINATIM_BASE_URL}/search', params={'q': f'{query}, India', 'format': 'json', 'limit': 1, 'countrycodes': 'in'})
            resp.raise_for_status()
            rows = resp.json()
            if rows:
                result = {'lat': float(rows[0]['lat']), 'lon': float(rows[0]['lon']), 'display_name': rows[0].get('display_name', query), 'source': 'nominatim'}
                geocode_cache.set(key, result, 86400)
                return result
    except Exception as exc:
        logger.warning('Nominatim unavailable (%s), using gazetteer fallback', exc)
    result = gazetteer_lookup(query) or {'lat': 22.9868, 'lon': 87.8550, 'display_name': f'{query} (approximate, West Bengal)', 'source': 'fallback'}
    geocode_cache.set(key, result, 3600)
    return result
