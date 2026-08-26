from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from utils.auth import current_user
from utils.db import db, clean
from utils.geo import NADIA, KOLKATA
from services.routing_service import get_route

router = APIRouter(prefix='/api')

@router.get('/orders/{order_id}/logistics')
async def order_logistics(order_id: str, user=Depends(current_user)):
    query = {'order_id': order_id} if user['role'] == 'admin' else {'order_id': order_id, '$or': [{'farmer_id': user['id']}, {'buyer_id': user['id']}]}
    order = await db.orders.find_one(query)
    if not order: raise HTTPException(404, 'Order not found.')
    p_lat, p_lon = order.get('pickup_lat') or NADIA[0], order.get('pickup_lon') or NADIA[1]
    d_lat, d_lon = order.get('delivery_lat') or KOLKATA[0], order.get('delivery_lon') or KOLKATA[1]
    farmer = buyer = None
    try: farmer = await db.users.find_one({'_id': ObjectId(order['farmer_id'])})
    except Exception: pass
    try: buyer = await db.users.find_one({'_id': ObjectId(order['buyer_id'])})
    except Exception: pass
    route = await get_route(p_lat, p_lon, d_lat, d_lon)
    return {
        'order': clean(order),
        'pickup': {'name': (farmer or {}).get('name', 'Farmer'), 'label': order.get('pickup_location', 'Nadia, West Bengal'), 'lat': p_lat, 'lon': p_lon},
        'delivery': {'name': (buyer or {}).get('business_name') or (buyer or {}).get('name', 'Buyer'), 'label': order.get('delivery_location', 'Kolkata'), 'lat': d_lat, 'lon': d_lon},
        'route': route,
    }
