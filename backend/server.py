from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / '.env')

import os, secrets, logging
from datetime import datetime, timezone, timedelta
from typing import Optional
import bcrypt, jwt
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument
from pydantic import BaseModel, Field, EmailStr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('khetsetu')
from utils.db import client, db, clean
from utils.auth import current_user
from utils.geo import haversine_km, NADIA, KOLKATA
from services.matching_service import compute_match
from services.routing_service import get_route
from services.geocoding_service import geocode
from routes.geo import router as geo_router
from routes.weather import router as weather_router
from routes.market import router as market_router
from routes.integrations import router as integrations_router
from routes.logistics import router as logistics_router

app = FastAPI(title='KhetSetu API')
api = APIRouter(prefix='/api')
SECRET = os.environ['JWT_SECRET']
ALGORITHM = 'HS256'

class AuthInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: Optional[str] = None
    role: Optional[str] = 'farmer'

class ProduceInput(BaseModel):
    crop: str = Field(min_length=2)
    quantity: float = Field(gt=0)
    unit: str = 'kg'
    grade: str = 'Grade A'
    harvest_date: str
    expected_price: float = Field(gt=0)
    location: str = 'Nadia, West Bengal'
    description: str = ''
    status: str = 'active'
    village: str = ''
    district: str = 'Nadia'
    state: str = 'West Bengal'
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class OrderInput(BaseModel):
    produce_id: str
    quantity: float = Field(gt=0)

class StatusInput(BaseModel):
    status: str

def hash_password(password): return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
def verify_password(password, hashed): return bcrypt.checkpw(password.encode(), hashed.encode())
def token(user_id, kind='access'):
    duration = timedelta(minutes=30) if kind == 'access' else timedelta(days=7)
    return jwt.encode({'sub': str(user_id), 'type': kind, 'exp': datetime.now(timezone.utc)+duration}, SECRET, algorithm=ALGORITHM)

def set_auth(response, user_id):
    secure = os.environ.get('COOKIE_SECURE', 'true').lower() == 'true'
    response.set_cookie('access_token', token(user_id), httponly=True, secure=secure, samesite='none' if secure else 'lax', max_age=1800)
    response.set_cookie('refresh_token', token(user_id, 'refresh'), httponly=True, secure=secure, samesite='none' if secure else 'lax', max_age=604800)

async def seed_demo():
    if await db.users.count_documents({}) > 0: return
    users = [
        {'email':'farmer@khetsetu.in','password_hash':hash_password('farmer123'),'name':'Arjun Das','role':'farmer','location':'Nadia, West Bengal','address':'Nadia, West Bengal','district':'Nadia','state':'West Bengal','latitude':NADIA[0],'longitude':NADIA[1]},
        {'email':'buyer@khetsetu.in','password_hash':hash_password('buyer123'),'name':'FreshMart Retail','role':'buyer','location':'Kolkata, West Bengal','business_name':'FreshMart Retail','address':'Sealdah, Kolkata, West Bengal','district':'Kolkata','state':'West Bengal','latitude':KOLKATA[0],'longitude':KOLKATA[1]},
        {'email':os.environ['ADMIN_EMAIL'],'password_hash':hash_password(os.environ['ADMIN_PASSWORD']),'name':'KhetSetu Admin','role':'admin','location':'India'}]
    result = await db.users.insert_many(users)
    farmer, buyer, _ = result.inserted_ids
    now = datetime.now(timezone.utc).isoformat()
    produce = [
        {'farmer_id':str(farmer),'crop':'Tomato','quantity':500,'unit':'kg','grade':'Grade A','harvest_date':'2026-03-28','expected_price':25,'location':'Nadia, West Bengal','status':'active','description':'Fresh field tomatoes, sorted and packed.','created_at':now},
        {'farmer_id':str(farmer),'crop':'Potato','quantity':800,'unit':'kg','grade':'Grade A','harvest_date':'2026-04-02','expected_price':19,'location':'Nadia, West Bengal','status':'active','description':'Washed table potatoes.','created_at':now},
        {'farmer_id':str(farmer),'crop':'Onion','quantity':300,'unit':'kg','grade':'Grade B','harvest_date':'2026-03-20','expected_price':22,'location':'Nadia, West Bengal','status':'draft','description':'Firm red onions.','created_at':now}]
    ids = (await db.produce.insert_many(produce)).inserted_ids
    orders=[]
    for i, status in enumerate(['pickup_scheduled','in_transit','completed','pending','delivered']):
        orders.append({'order_id':f'KS-2026-00{125+i}','farmer_id':str(farmer),'buyer_id':str(buyer),'produce_id':str(ids[0 if i<2 else 1]),'product':'Tomato' if i<2 else 'Potato','quantity':500 if i<2 else 200,'price':25 if i<2 else 19,'transport_cost':1500 if i<2 else 900,'pickup_location':'Nadia, West Bengal','delivery_location':'Kolkata','status':status,'created_at':now,'updated_at':now})
    await db.orders.insert_many(orders)
    notices=[('FreshMart requested 500 kg Tomato.','order'),('Order KS-2026-00125 accepted.','order'),('Rahul Logistics assigned to your pickup.','logistics'),('Pickup scheduled for tomorrow morning.','logistics'),('KhetSetu market recommendation updated.','insight')]
    await db.notifications.insert_many([{'user_id':str(farmer),'title':t,'kind':k,'read':False,'created_at':now} for t,k in notices])

async def ensure_geo():
    await db.users.update_many({'role':'farmer','latitude':{'$exists':False}},{'$set':{'latitude':NADIA[0],'longitude':NADIA[1],'district':'Nadia','state':'West Bengal','address':'Nadia, West Bengal'}})
    await db.users.update_many({'role':'buyer','latitude':{'$exists':False}},{'$set':{'latitude':KOLKATA[0],'longitude':KOLKATA[1],'district':'Kolkata','state':'West Bengal','address':'Sealdah, Kolkata, West Bengal','business_name':'FreshMart Retail'}})
    await db.produce.update_many({'latitude':{'$exists':False}},{'$set':{'latitude':NADIA[0],'longitude':NADIA[1],'district':'Nadia','state':'West Bengal'}})
    await db.orders.update_many({'pickup_lat':{'$exists':False}},{'$set':{'pickup_lat':NADIA[0],'pickup_lon':NADIA[1],'delivery_lat':KOLKATA[0],'delivery_lon':KOLKATA[1]}})
    if await db.markets.count_documents({}) == 0:
        await db.markets.insert_many([
            {'name':'Kalyani Krishi Mandi','location':'Kalyani, Nadia, West Bengal','district':'Nadia','state':'West Bengal','latitude':22.9750,'longitude':88.4345},
            {'name':'Sealdah Koley Market','location':'Kolkata, West Bengal','district':'Kolkata','state':'West Bengal','latitude':22.5697,'longitude':88.3697},
            {'name':'Krishnanagar Bazar','location':'Krishnanagar, Nadia, West Bengal','district':'Nadia','state':'West Bengal','latitude':23.4058,'longitude':88.4907},
            {'name':'Barasat Haat','location':'Barasat, West Bengal','district':'North 24 Parganas','state':'West Bengal','latitude':22.7228,'longitude':88.4800}])

@app.on_event('startup')
async def startup():
    await db.users.create_index('email', unique=True)
    await seed_demo()
    await ensure_geo()

@api.get('/')
async def root(): return {'name':'KhetSetu','status':'ready'}

@api.post('/auth/register')
async def register(data: AuthInput, response: Response):
    email=data.email.lower()
    if await db.users.find_one({'email':email}): raise HTTPException(409,'An account with this email already exists.')
    role=data.role if data.role in ['farmer','buyer'] else 'farmer'
    result=await db.users.insert_one({'email':email,'password_hash':hash_password(data.password),'name':data.name or email.split('@')[0].title(),'role':role,'location':'India'})
    user=clean(await db.users.find_one({'_id':result.inserted_id},{'password_hash':0})); set_auth(response,result.inserted_id); return user

@api.post('/auth/login')
async def login(data: AuthInput, response: Response):
    user=await db.users.find_one({'email':data.email.lower()})
    if not user or not verify_password(data.password,user['password_hash']): raise HTTPException(401,'Email or password is incorrect.')
    set_auth(response,user['_id']); return clean({k:v for k,v in user.items() if k!='password_hash'})

@api.post('/auth/logout')
async def logout(response: Response): response.delete_cookie('access_token'); response.delete_cookie('refresh_token'); return {'message':'Logged out'}

@api.get('/auth/me')
async def me(user=Depends(current_user)): return user

@api.post('/auth/forgot-password')
async def forgot(data: dict): return {'message':'If that email exists, reset instructions are ready for the account.'}

@api.get('/dashboard')
async def dashboard(user=Depends(current_user)):
    uid=user['id']; produce=await db.produce.find({'farmer_id':uid}).to_list(100); orders=await db.orders.find({'farmer_id':uid}).to_list(100)
    completed=[o for o in orders if o['status']=='completed']; earnings=sum(o['quantity']*o['price']+o.get('transport_cost',0) for o in completed)
    return {'user':user,'stats':{'active_produce':sum(1 for p in produce if p.get('status')=='active'),'pending_orders':sum(1 for o in orders if o.get('status') not in ['completed','cancelled']),'monthly_earnings':earnings or 48500,'farmer_share':64},'produce':[clean(p) for p in produce],'orders':[clean(o) for o in orders]}

@api.get('/produce')
async def list_produce(user=Depends(current_user), search=''):
    query={'crop':{'$regex':search,'$options':'i'}} if search else {}
    if user['role']=='farmer': query['farmer_id']=user['id']
    return [clean(p) for p in await db.produce.find(query).sort('created_at',-1).to_list(100)]

@api.post('/produce')
async def add_produce(data: ProduceInput, user=Depends(current_user)):
    doc=data.model_dump(); doc.update({'farmer_id':user['id'],'created_at':datetime.now(timezone.utc).isoformat()})
    if doc.get('latitude') is None or doc.get('longitude') is None:
        place=', '.join(x for x in [doc.get('village'), doc.get('district'), doc.get('state')] if x) or doc['location']
        geo=await geocode(place)
        doc['latitude'], doc['longitude'], doc['geocode_source'] = geo['lat'], geo['lon'], geo['source']
    result=await db.produce.insert_one(doc); return clean(await db.produce.find_one({'_id':result.inserted_id}))

@api.delete('/produce/{produce_id}')
async def delete_produce(produce_id: str, user=Depends(current_user)):
    from bson import ObjectId
    result=await db.produce.delete_one({'_id':ObjectId(produce_id),'farmer_id':user['id']})
    if not result.deleted_count: raise HTTPException(404,'Produce listing not found.')
    return {'message':'Listing deleted'}

@api.get('/marketplace')
async def marketplace(user=Depends(current_user), search=''):
    query={'status':'active'}
    if search: query['$or']=[{'crop':{'$regex':search,'$options':'i'}},{'location':{'$regex':search,'$options':'i'}}]
    items=[clean(p) for p in await db.produce.find(query).to_list(100)]
    buyer=await db.users.find_one({'role':'buyer'}) or {}
    b_lat,b_lon=buyer.get('latitude',KOLKATA[0]),buyer.get('longitude',KOLKATA[1])
    for p in items:
        lat,lon=p.get('latitude') or NADIA[0],p.get('longitude') or NADIA[1]
        distance_km=round(haversine_km(lat,lon,b_lat,b_lon)*1.25,1)
        match=compute_match(p,distance_km)
        p.update({'buyer':buyer.get('business_name') or buyer.get('name','FreshMart Retail'),'latitude':lat,'longitude':lon,
                  'distance':f'{distance_km} km','distance_km':distance_km,'match_score':match['score'],
                  'match_explanation':match['explanation'],'match_factors':match['factors']})
    return items

@api.post('/orders')
async def create_order(data: OrderInput, user=Depends(current_user)):
    from bson import ObjectId
    p=await db.produce.find_one({'_id':ObjectId(data.produce_id)})
    if not p: raise HTTPException(404,'Produce listing not found.')
    buyer=user if user['role']=='buyer' else clean(await db.users.find_one({'role':'buyer'}))
    p_lat,p_lon=p.get('latitude') or NADIA[0],p.get('longitude') or NADIA[1]
    d_lat,d_lon=buyer.get('latitude') or KOLKATA[0],buyer.get('longitude') or KOLKATA[1]
    route=await get_route(p_lat,p_lon,d_lat,d_lon)
    doc={'order_id':f'KS-{datetime.now().year}-{secrets.randbelow(90000)+10000}','farmer_id':p['farmer_id'],'buyer_id':buyer['id'],'produce_id':data.produce_id,'product':p['crop'],'quantity':data.quantity,'price':p['expected_price'],'transport_cost':route['transport_cost'],'distance_km':route['distance_km'],'eta_min':route['duration_min'],'pickup_location':p['location'],'delivery_location':buyer.get('address') or 'Kolkata','pickup_lat':p_lat,'pickup_lon':p_lon,'delivery_lat':d_lat,'delivery_lon':d_lon,'status':'pending','created_at':datetime.now(timezone.utc).isoformat(),'updated_at':datetime.now(timezone.utc).isoformat()}
    result=await db.orders.insert_one(doc); return clean(await db.orders.find_one({'_id':result.inserted_id}))

@api.get('/orders')
async def list_orders(user=Depends(current_user)):
    query={} if user['role']=='admin' else {'$or':[{'farmer_id':user['id']},{'buyer_id':user['id']}]}
    return [clean(o) for o in await db.orders.find(query).sort('created_at',-1).to_list(100)]

@api.patch('/orders/{order_id}/status')
async def update_order(order_id: str, data: StatusInput, user=Depends(current_user)):
    allowed=['pending','accepted','pickup_scheduled','in_transit','delivered','completed','cancelled']
    if data.status not in allowed: raise HTTPException(400,'That order status is not available.')
    query={'order_id':order_id} if user['role']=='admin' else {'order_id':order_id,'$or':[{'farmer_id':user['id']},{'buyer_id':user['id']}]}
    result=await db.orders.find_one_and_update(query,{'$set':{'status':data.status,'updated_at':datetime.now(timezone.utc).isoformat()}},return_document=ReturnDocument.AFTER)
    if not result: raise HTTPException(404,'Order not found.')
    await db.notifications.insert_one({'user_id':user['id'],'title':f'Order {order_id} updated to {data.status.replace("_"," ")}.','kind':'order','read':False,'created_at':datetime.now(timezone.utc).isoformat()})
    return clean(result)

@api.get('/notifications')
async def notifications(user=Depends(current_user)): return [clean(n) for n in await db.notifications.find({'user_id':user['id']}).sort('created_at',-1).to_list(100)]
@api.patch('/notifications/read')
async def read_notifications(user=Depends(current_user)): await db.notifications.update_many({'user_id':user['id']},{'$set':{'read':True}}); return {'message':'Notifications marked as read'}

@api.get('/prices')
async def prices(user=Depends(current_user)): return [{'crop':'Tomato','price':28,'previous':26,'demand':'+12%','range':'₹29–₹32'},{'crop':'Potato','price':19,'previous':20,'demand':'+4%','range':'₹20–₹22'},{'crop':'Onion','price':22,'previous':21,'demand':'+8%','range':'₹23–₹25'}]
@api.get('/admin/metrics')
async def admin_metrics(user=Depends(current_user)):
    if user['role']!='admin': raise HTTPException(403,'Admin access required.')
    return {'farmers':1248,'buyers':326,'listings':2840,'orders':486,'farmer_share':64.8,'price_gap':11.4}
@api.post('/demo/reset')
async def reset_demo(user=Depends(current_user)):
    if user['role']!='admin': raise HTTPException(403,'Admin access required.')
    await db.users.delete_many({}); await db.produce.delete_many({}); await db.orders.delete_many({}); await db.notifications.delete_many({}); await seed_demo(); return {'message':'Demo data restored'}

app.include_router(api)
app.include_router(geo_router)
app.include_router(weather_router)
app.include_router(market_router)
app.include_router(integrations_router)
app.include_router(logistics_router)

_default_origins = [os.environ.get('FRONTEND_URL',''), 'https://khetsetu.in', 'https://www.khetsetu.in', 'http://localhost:3000']
_extra = [o.strip() for o in os.environ.get('ALLOWED_ORIGINS','').split(',') if o.strip() and o.strip() != '*']
trusted_origins = sorted({o for o in _default_origins + _extra if o})

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=trusted_origins,
    allow_origin_regex=r'https://.*\.preview\.emergentagent\.com',
    allow_methods=['GET','POST','PUT','PATCH','DELETE','OPTIONS'],
    allow_headers=['Content-Type','Authorization','Accept','Origin','X-Requested-With'],
)

@app.on_event('shutdown')
async def shutdown(): client.close()