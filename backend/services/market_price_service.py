from datetime import date
from config.settings import MARKET_API_KEY
from utils.cache import market_cache

DEMO_ROWS = [
    {'crop': 'Tomato', 'market': 'Kalyani Krishi Mandi', 'location': 'Kalyani, Nadia, West Bengal', 'price': 28, 'unit': '₹/kg', 'demand': 12, 'previous': 26, 'range': '₹29–₹32'},
    {'crop': 'Tomato', 'market': 'Sealdah Koley Market', 'location': 'Kolkata, West Bengal', 'price': 31, 'unit': '₹/kg', 'demand': 14, 'previous': 29, 'range': '₹30–₹34'},
    {'crop': 'Potato', 'market': 'Kalyani Krishi Mandi', 'location': 'Kalyani, Nadia, West Bengal', 'price': 19, 'unit': '₹/kg', 'demand': 4, 'previous': 20, 'range': '₹20–₹22'},
    {'crop': 'Potato', 'market': 'Barasat Haat', 'location': 'Barasat, West Bengal', 'price': 21, 'unit': '₹/kg', 'demand': 5, 'previous': 20, 'range': '₹20–₹23'},
    {'crop': 'Onion', 'market': 'Krishnanagar Bazar', 'location': 'Krishnanagar, Nadia, West Bengal', 'price': 22, 'unit': '₹/kg', 'demand': 8, 'previous': 21, 'range': '₹23–₹25'},
    {'crop': 'Onion', 'market': 'Sealdah Koley Market', 'location': 'Kolkata, West Bengal', 'price': 24, 'unit': '₹/kg', 'demand': 9, 'previous': 23, 'range': '₹24–₹26'},
    {'crop': 'Rice', 'market': 'Krishnanagar Bazar', 'location': 'Krishnanagar, Nadia, West Bengal', 'price': 38, 'unit': '₹/kg', 'demand': 6, 'previous': 38, 'range': '₹38–₹41'},
    {'crop': 'Wheat', 'market': 'Barasat Haat', 'location': 'Barasat, West Bengal', 'price': 27, 'unit': '₹/kg', 'demand': 3, 'previous': 26, 'range': '₹26–₹29'},
]

async def get_prices(crop=None, location=None, date_str=None):
    key = f'{crop or ""}|{location or ""}|{date_str or ""}'.lower()
    cached = market_cache.get(key)
    if cached: return cached
    # Architecture hook: when a verified government/agri API is connected via
    # MARKET_API_KEY, fetch live rows here and keep the same response shape.
    rows = [dict(r, date=date_str or date.today().isoformat(), source='Demo / Prototype Data') for r in DEMO_ROWS]
    if crop: rows = [r for r in rows if crop.lower() in r['crop'].lower()]
    if location: rows = [r for r in rows if location.lower() in r['location'].lower() or location.lower() in r['market'].lower()]
    result = {'rows': rows, 'source': 'demo', 'demo': True, 'external_configured': bool(MARKET_API_KEY)}
    market_cache.set(key, result, 3600)
    return result

def price_for_crop(crop):
    rows = [r for r in DEMO_ROWS if r['crop'].lower() == (crop or '').lower()]
    return min(r['price'] for r in rows) if rows else None

def demand_for_crop(crop):
    rows = [r for r in DEMO_ROWS if r['crop'].lower() == (crop or '').lower()]
    return max(r['demand'] for r in rows) if rows else None
