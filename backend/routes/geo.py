from fastapi import APIRouter, Depends
from utils.auth import current_user
from utils.db import db, clean
from utils.geo import haversine_km, NADIA, KOLKATA
from services.geocoding_service import geocode
from services.routing_service import get_route
from services.matching_service import compute_match

router = APIRouter(prefix='/api')

@router.get('/geo/geocode')
async def geocode_place(q: str):
    return await geocode(q)

@router.get('/geo/route')
async def route(from_lat: float, from_lon: float, to_lat: float, to_lon: float):
    return await get_route(from_lat, from_lon, to_lat, to_lon)

@router.get('/map/overview')
async def map_overview(user=Depends(current_user)):
    buyer = await db.users.find_one({'role': 'buyer'})
    b_lat, b_lon = (buyer or {}).get('latitude', KOLKATA[0]), (buyer or {}).get('longitude', KOLKATA[1])
    listings = []
    for p in await db.produce.find({'status': 'active'}).to_list(200):
        p = clean(p)
        lat, lon = p.get('latitude') or NADIA[0], p.get('longitude') or NADIA[1]
        distance_km = round(haversine_km(lat, lon, b_lat, b_lon) * 1.25, 1)
        match = compute_match(p, distance_km)
        listings.append({'id': p['id'], 'crop': p['crop'], 'quantity': p['quantity'], 'unit': p['unit'],
                         'expected_price': p['expected_price'], 'location': p['location'], 'latitude': lat,
                         'longitude': lon, 'distance_km': distance_km, 'match_score': match['score'],
                         'match_explanation': match['explanation']})
    buyers = [{'id': clean(b)['id'], 'name': b.get('business_name') or b.get('name'), 'address': b.get('address', ''),
               'district': b.get('district', ''), 'state': b.get('state', ''),
               'latitude': b.get('latitude', KOLKATA[0]), 'longitude': b.get('longitude', KOLKATA[1])}
              for b in await db.users.find({'role': 'buyer'}).to_list(100)]
    markets = [clean(m) for m in await db.markets.find({}).to_list(100)]
    return {'listings': listings, 'buyers': buyers, 'markets': markets}
