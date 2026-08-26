import os

MAP_API_KEY = os.environ.get('MAP_API_KEY', '')
WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY', '')
MARKET_API_KEY = os.environ.get('MARKET_API_KEY', '')
OSRM_BASE_URL = os.environ.get('OSRM_BASE_URL', 'https://router.project-osrm.org')
NOMINATIM_BASE_URL = os.environ.get('NOMINATIM_BASE_URL', 'https://nominatim.openstreetmap.org')
OPEN_METEO_BASE_URL = os.environ.get('OPEN_METEO_BASE_URL', 'https://api.open-meteo.com')
HTTP_TIMEOUT = float(os.environ.get('EXTERNAL_API_TIMEOUT', '6'))
USER_AGENT = 'KhetSetu-SIH-Prototype/1.0'
