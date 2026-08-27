import hashlib
from datetime import date, datetime, timezone, timedelta
from config.settings import MARKET_API_KEY
from utils.cache import market_cache

BASE_ROWS = [
    {'crop': 'Tomato', 'market': 'Kalyani Krishi Mandi', 'location': 'Kalyani, Nadia, West Bengal', 'base': 28, 'unit': '₹/kg', 'demand': 12},
    {'crop': 'Tomato', 'market': 'Sealdah Koley Market', 'location': 'Kolkata, West Bengal', 'base': 31, 'unit': '₹/kg', 'demand': 14},
    {'crop': 'Potato', 'market': 'Kalyani Krishi Mandi', 'location': 'Kalyani, Nadia, West Bengal', 'base': 19, 'unit': '₹/kg', 'demand': 4},
    {'crop': 'Potato', 'market': 'Barasat Haat', 'location': 'Barasat, West Bengal', 'base': 21, 'unit': '₹/kg', 'demand': 5},
    {'crop': 'Onion', 'market': 'Krishnanagar Bazar', 'location': 'Krishnanagar, Nadia, West Bengal', 'base': 22, 'unit': '₹/kg', 'demand': 8},
    {'crop': 'Onion', 'market': 'Sealdah Koley Market', 'location': 'Kolkata, West Bengal', 'base': 24, 'unit': '₹/kg', 'demand': 9},
    {'crop': 'Carrot', 'market': 'Sealdah Koley Market', 'location': 'Kolkata, West Bengal', 'base': 32, 'unit': '₹/kg', 'demand': 7},
    {'crop': 'Cabbage', 'market': 'Barasat Haat', 'location': 'Barasat, West Bengal', 'base': 17, 'unit': '₹/kg', 'demand': 5},
    {'crop': 'Cauliflower', 'market': 'Kalyani Krishi Mandi', 'location': 'Kalyani, Nadia, West Bengal', 'base': 27, 'unit': '₹/kg', 'demand': 9},
    {'crop': 'Green Chili', 'market': 'Krishnanagar Bazar', 'location': 'Krishnanagar, Nadia, West Bengal', 'base': 60, 'unit': '₹/kg', 'demand': 11},
    {'crop': 'Brinjal', 'market': 'Barasat Haat', 'location': 'Barasat, West Bengal', 'base': 23, 'unit': '₹/kg', 'demand': 6},
]

SOURCE_LABEL = 'Simulated live pricing (API-ready)'

def _wobble(crop, salt):
    h = int(hashlib.md5(f'{crop}|{salt}'.encode()).hexdigest()[:8], 16)
    return (h % 1300 - 650) / 10000  # deterministic ±6.5%

def _priced(row):
    now = datetime.now(timezone.utc)
    cur = round(row['base'] * (1 + _wobble(row['crop'] + row['market'], now.strftime('%Y%m%d%H'))), 1)
    prev = round(row['base'] * (1 + _wobble(row['crop'] + row['market'], (now - timedelta(hours=1)).strftime('%Y%m%d%H'))), 1)
    trend = round((cur - prev) / prev * 100, 1) if prev else 0.0
    return {'crop': row['crop'], 'market': row['market'], 'location': row['location'], 'price': cur, 'previous': prev,
            'trend_pct': trend, 'unit': row['unit'], 'demand': row['demand'],
            'range': f"₹{round(cur * 0.98)}–₹{round(cur * 1.1)}", 'last_updated': now.isoformat(), 'source': SOURCE_LABEL}

async def get_prices(crop=None, location=None, date_str=None):
    key = f'{crop or ""}|{location or ""}|{date_str or ""}'.lower()
    cached = market_cache.get(key)
    if cached: return cached
    # Architecture hook: when a verified government/agri API is connected via
    # MARKET_API_KEY, fetch live rows here and keep the same response shape.
    rows = [dict(_priced(r), date=date_str or date.today().isoformat()) for r in BASE_ROWS]
    if crop: rows = [r for r in rows if crop.lower() in r['crop'].lower()]
    if location: rows = [r for r in rows if location.lower() in r['location'].lower() or location.lower() in r['market'].lower()]
    result = {'rows': rows, 'source': 'simulated', 'demo': True, 'external_configured': bool(MARKET_API_KEY)}
    market_cache.set(key, result, 300)
    return result

def current_market_price(crop):
    rows = [r for r in BASE_ROWS if r['crop'].lower() == (crop or '').lower()]
    if not rows: return None
    best = min((_priced(r) for r in rows), key=lambda r: r['price'])
    return best

def price_for_crop(crop):
    row = current_market_price(crop)
    return row['price'] if row else None

def demand_for_crop(crop):
    rows = [r for r in BASE_ROWS if r['crop'].lower() == (crop or '').lower()]
    return max(r['demand'] for r in rows) if rows else None
