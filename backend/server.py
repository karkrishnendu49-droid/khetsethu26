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
from config.crops import crop_image, availability

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

SEED_VERSION = 'v2'
async def seed_demo():
    marker = await db.meta.find_one({'key': 'seed_version'})
    if marker and marker.get('value') == SEED_VERSION: return
    for col in ['users','produce','orders','notifications','password_reset_tokens','markets']:
        await db[col].delete_many({})
    users = [
        {'email':'farmer@khetsetu.in','password_hash':hash_password('farmer123'),'name':'Arjun Das','role':'farmer','location':'Nadia, West Bengal','address':'Nadia, West Bengal','district':'Nadia','state':'West Bengal','latitude':NADIA[0],'longitude':NADIA[1]},
        {'email':'meena@khetsetu.in','password_hash':hash_password('farmer123'),'name':'Meena Devi','role':'farmer','location':'Hooghly, West Bengal','address':'Hooghly, West Bengal','district':'Hooghly','state':'West Bengal','latitude':22.9089,'longitude':88.3967},
        {'email':'rafiq@khetsetu.in','password_hash':hash_password('farmer123'),'name':'Rafiq Mondal','role':'farmer','location':'Bardhaman, West Bengal','address':'Bardhaman, West Bengal','district':'Bardhaman','state':'West Bengal','latitude':23.2324,'longitude':87.8615},
        {'email':'buyer@khetsetu.in','password_hash':hash_password('buyer123'),'name':'FreshMart Retail','role':'buyer','location':'Kolkata, West Bengal','business_name':'FreshMart Retail','address':'Sealdah, Kolkata, West Bengal','district':'Kolkata','state':'West Bengal','latitude':KOLKATA[0],'longitude':KOLKATA[1]},
        {'email':os.environ['ADMIN_EMAIL'],'password_hash':hash_password(os.environ['ADMIN_PASSWORD']),'name':'KhetSetu Admin','role':'admin','location':'India'}]
    result = await db.users.insert_many(users)
    arjun, meena, rafiq, buyer, _ = [str(i) for i in result.inserted_ids]
    now = datetime.now(timezone.utc).isoformat()
    def prod(fid, fname, crop, qty, price, grade, loc, dist, lat, lon, desc, harvest):
        return {'farmer_id':fid,'farmer_name':fname,'crop':crop,'image':crop_image(crop),'quantity':qty,'unit':'kg','grade':grade,'harvest_date':harvest,'expected_price':price,'location':loc,'district':dist,'state':'West Bengal','latitude':lat,'longitude':lon,'status':'active','description':desc,'created_at':now}
    produce = [
        prod(arjun,'Arjun Das','Tomato',500,25,'Grade A','Nadia, West Bengal','Nadia',NADIA[0],NADIA[1],'Fresh field tomatoes, sorted and packed.','2026-06-05'),
        prod(arjun,'Arjun Das','Potato',800,19,'Grade A','Nadia, West Bengal','Nadia',NADIA[0],NADIA[1],'Washed table potatoes.','2026-06-02'),
        prod(arjun,'Arjun Das','Green Chili',120,55,'Grade A','Nadia, West Bengal','Nadia',NADIA[0],NADIA[1],'Hot green chilies, freshly picked.','2026-06-08'),
        prod(meena,'Meena Devi','Carrot',250,28,'Grade A','Hooghly, West Bengal','Hooghly',22.9089,88.3967,'Sweet orange carrots with tops.','2026-06-06'),
        prod(meena,'Meena Devi','Cabbage',400,15,'Grade B','Hooghly, West Bengal','Hooghly',22.9089,88.3967,'Firm green cabbage heads.','2026-06-04'),
        prod(rafiq,'Rafiq Mondal','Onion',300,22,'Grade B','Bardhaman, West Bengal','Bardhaman',23.2324,87.8615,'Firm red onions.','2026-06-01'),
        prod(rafiq,'Rafiq Mondal','Cauliflower',350,24,'Grade A','Bardhaman, West Bengal','Bardhaman',23.2324,87.8615,'Compact white cauliflower.','2026-06-07'),
        prod(rafiq,'Rafiq Mondal','Brinjal',200,21,'Grade A','Bardhaman, West Bengal','Bardhaman',23.2324,87.8615,'Glossy purple brinjal.','2026-06-05')]
    ids = (await db.produce.insert_many(produce)).inserted_ids
    orders=[]
    for i, status in enumerate(['placed','accepted','preparing','out_for_delivery','delivered']):
        orders.append({'order_id':f'KS-2026-00{125+i}','farmer_id':arjun,'buyer_id':buyer,'buyer_name':'FreshMart Retail','farmer_name':'Arjun Das','produce_id':str(ids[0 if i<2 else 1]),'product':'Tomato' if i<2 else 'Potato','quantity':100 if i<2 else 200,'price':25 if i<2 else 19,'transport_cost':1750,'distance_km':115.7,'eta_min':104,'pickup_location':'Nadia, West Bengal','delivery_location':'Sealdah, Kolkata, West Bengal','pickup_lat':NADIA[0],'pickup_lon':NADIA[1],'delivery_lat':KOLKATA[0],'delivery_lon':KOLKATA[1],'status':status,'created_at':now,'updated_at':now})
    await db.orders.insert_many(orders)
    await db.notifications.insert_many([
        {'user_id':arjun,'title':'New order received: 100 kg Tomato from FreshMart Retail.','kind':'order','read':False,'created_at':now},
        {'user_id':arjun,'title':'KhetSetu market recommendation updated.','kind':'insight','read':False,'created_at':now},
        {'user_id':buyer,'title':'Your order KS-2026-00126 was accepted by Arjun Das.','kind':'order','read':False,'created_at':now},
        {'user_id':buyer,'title':'Order KS-2026-00128 is out for delivery.','kind':'order','read':False,'created_at':now}])
    await db.meta.update_one({'key':'seed_version'},{'$set':{'value':SEED_VERSION}},upsert=True)

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
    await db.password_reset_tokens.create_index('expires_at', expireAfterSeconds=0)
    await seed_demo()
    await ensure_geo()

@api.get('/')
async def root(): return {'name':'KhetSetu','status':'ready'}

@api.post('/auth/register')
async def register(data: AuthInput, response: Response):
    email=data.email.lower()
    if not data.name or len(data.name.strip())<2: raise HTTPException(400,'Please enter your full name.')
    if data.role not in ['farmer','buyer']: raise HTTPException(400,'Please choose whether you are a farmer or a buyer.')
    if await db.users.find_one({'email':email}): raise HTTPException(409,'An account with this email already exists.')
    coords={'latitude':NADIA[0],'longitude':NADIA[1],'district':'Nadia','state':'West Bengal','address':'Nadia, West Bengal'} if data.role=='farmer' else {'latitude':KOLKATA[0],'longitude':KOLKATA[1],'district':'Kolkata','state':'West Bengal','address':'Kolkata, West Bengal','business_name':data.name.strip()}
    result=await db.users.insert_one({'email':email,'password_hash':hash_password(data.password),'name':data.name.strip(),'role':data.role,'location':coords['address'],**coords})
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

class ForgotInput(BaseModel):
    email: EmailStr

class ResetInput(BaseModel):
    token: str
    new_password: str = Field(min_length=6)

@api.post('/auth/forgot-password')
async def forgot(data: ForgotInput):
    user=await db.users.find_one({'email':data.email.lower()})
    if not user:
        return {'message':'If that email exists, a reset code has been generated.','demo':True}
    reset_token=secrets.token_urlsafe(24)
    await db.password_reset_tokens.insert_one({'token':reset_token,'user_id':str(user['_id']),'email':data.email.lower(),'expires_at':datetime.now(timezone.utc)+timedelta(hours=1),'used':False})
    return {'message':'Reset code generated. In this SIH prototype it is shown here instead of being emailed.','reset_token':reset_token,'demo':True}

@api.post('/auth/reset-password')
async def reset_password(data: ResetInput):
    doc=await db.password_reset_tokens.find_one({'token':data.token})
    if not doc or doc.get('used'): raise HTTPException(400,'This reset code is invalid or was already used.')
    expires=doc['expires_at'].replace(tzinfo=timezone.utc) if doc['expires_at'].tzinfo is None else doc['expires_at']
    if expires < datetime.now(timezone.utc): raise HTTPException(400,'This reset code has expired. Please request a new one.')
    from bson import ObjectId
    await db.users.update_one({'_id':ObjectId(doc['user_id'])},{'$set':{'password_hash':hash_password(data.new_password)}})
    await db.password_reset_tokens.update_one({'token':data.token},{'$set':{'used':True}})
    return {'message':'Password updated. You can log in with your new password.'}

@api.get('/dashboard')
async def dashboard(user=Depends(current_user)):
    uid=user['id']
    if user['role']=='buyer':
        orders=await db.orders.find({'buyer_id':uid}).sort('created_at',-1).to_list(200)
        active=[o for o in orders if o.get('status') in ['placed','accepted','preparing','out_for_delivery']]
        delivered=[o for o in orders if o.get('status')=='delivered']
        spent=sum(o['quantity']*o['price']+o.get('transport_cost',0) for o in delivered)
        featured=[clean(p) for p in await db.produce.find({'status':'active','quantity':{'$gt':0}}).limit(4).to_list(4)]
        return {'user':user,'role':'buyer','stats':{'available_produce':await db.produce.count_documents({'status':'active','quantity':{'$gt':0}}),'active_orders':len(active),'completed_orders':len(delivered),'total_spent':spent},'orders':[clean(o) for o in orders[:8]],'produce':featured}
    produce=await db.produce.find({'farmer_id':uid}).to_list(100); orders=await db.orders.find({'farmer_id':uid}).sort('created_at',-1).to_list(200)
    delivered=[o for o in orders if o.get('status')=='delivered']; earnings=sum(o['quantity']*o['price'] for o in delivered)
    return {'user':user,'role':user['role'],'stats':{'total_produce':len(produce),'active_produce':sum(1 for p in produce if p.get('status')=='active'),'pending_orders':sum(1 for o in orders if o.get('status')=='placed'),'completed_orders':len(delivered),'monthly_earnings':earnings,'farmer_share':64},'produce':[clean(p) for p in produce],'orders':[clean(o) for o in orders[:8]]}

@api.get('/produce')
async def list_produce(user=Depends(current_user), search=''):
    query={'crop':{'$regex':search,'$options':'i'}} if search else {}
    if user['role']=='farmer': query['farmer_id']=user['id']
    return [clean(p) for p in await db.produce.find(query).sort('created_at',-1).to_list(100)]

@api.post('/produce')
async def add_produce(data: ProduceInput, user=Depends(current_user)):
    if user['role']!='farmer': raise HTTPException(403,'Only farmers can add produce.')
    doc=data.model_dump(); doc.update({'farmer_id':user['id'],'farmer_name':user['name'],'image':crop_image(doc['crop']),'created_at':datetime.now(timezone.utc).isoformat()})
    if doc.get('latitude') is None or doc.get('longitude') is None:
        place=', '.join(x for x in [doc.get('village'), doc.get('district'), doc.get('state')] if x) or doc['location']
        geo=await geocode(place)
        doc['latitude'], doc['longitude'], doc['geocode_source'] = geo['lat'], geo['lon'], geo['source']
    result=await db.produce.insert_one(doc); return clean(await db.produce.find_one({'_id':result.inserted_id}))

@api.put('/produce/{produce_id}')
async def edit_produce(produce_id: str, data: ProduceInput, user=Depends(current_user)):
    if user['role']!='farmer': raise HTTPException(403,'Only farmers can edit produce.')
    from bson import ObjectId
    doc=data.model_dump(); doc['image']=crop_image(doc['crop']); doc['updated_at']=datetime.now(timezone.utc).isoformat()
    result=await db.produce.find_one_and_update({'_id':ObjectId(produce_id),'farmer_id':user['id']},{'$set':doc},return_document=ReturnDocument.AFTER)
    if not result: raise HTTPException(404,'Produce listing not found.')
    return clean(result)

@api.get('/produce/{produce_id}')
async def get_produce(produce_id: str, user=Depends(current_user)):
    from bson import ObjectId
    p=await db.produce.find_one({'_id':ObjectId(produce_id)})
    if not p: raise HTTPException(404,'Produce listing not found.')
    return clean(p)

@api.delete('/produce/{produce_id}')
async def delete_produce(produce_id: str, user=Depends(current_user)):
    if user['role']!='farmer': raise HTTPException(403,'Only farmers can delete produce.')
    from bson import ObjectId
    result=await db.produce.delete_one({'_id':ObjectId(produce_id),'farmer_id':user['id']})
    if not result.deleted_count: raise HTTPException(404,'Produce listing not found.')
    return {'message':'Listing deleted'}

@api.get('/marketplace')
async def marketplace(user=Depends(current_user), search='', crop='', max_price: Optional[float]=None, district='', available_only: bool=False):
    from services.market_price_service import current_market_price
    query={'status':'active'}
    if search: query['$or']=[{'crop':{'$regex':search,'$options':'i'}},{'location':{'$regex':search,'$options':'i'}},{'farmer_name':{'$regex':search,'$options':'i'}}]
    if crop: query['crop']=crop
    if max_price is not None: query['expected_price']={'$lte':max_price}
    if district: query['district']={'$regex':district,'$options':'i'}
    if available_only: query['quantity']={'$gt':0}
    items=[clean(p) for p in await db.produce.find(query).sort('created_at',-1).to_list(100)]
    ref_lat=user.get('latitude') or KOLKATA[0]; ref_lon=user.get('longitude') or KOLKATA[1]
    for p in items:
        lat,lon=p.get('latitude') or NADIA[0],p.get('longitude') or NADIA[1]
        distance_km=round(haversine_km(lat,lon,ref_lat,ref_lon)*1.25,1)
        match=compute_match(p,distance_km)
        mp=current_market_price(p['crop'])
        p.update({'image':p.get('image') or crop_image(p['crop']),'farmer_name':p.get('farmer_name','Farmer'),'availability':availability(p.get('quantity')),
                  'latitude':lat,'longitude':lon,'distance':f'{distance_km} km','distance_km':distance_km,'match_score':match['score'],
                  'match_explanation':match['explanation'],'match_factors':match['factors'],
                  'market_price':mp['price'] if mp else None,'market_trend_pct':mp['trend_pct'] if mp else None,'market_updated':mp['last_updated'] if mp else None})
    return items

@api.post('/orders')
async def create_order(data: OrderInput, user=Depends(current_user)):
    if user['role']!='buyer': raise HTTPException(403,'Only buyers can place orders.')
    from bson import ObjectId
    p=await db.produce.find_one({'_id':ObjectId(data.produce_id)})
    if not p: raise HTTPException(404,'Produce listing not found.')
    if data.quantity > float(p.get('quantity') or 0): raise HTTPException(400,f"Only {p.get('quantity',0)} {p.get('unit','kg')} available for this listing.")
    p_lat,p_lon=p.get('latitude') or NADIA[0],p.get('longitude') or NADIA[1]
    d_lat,d_lon=user.get('latitude') or KOLKATA[0],user.get('longitude') or KOLKATA[1]
    route=await get_route(p_lat,p_lon,d_lat,d_lon)
    now=datetime.now(timezone.utc).isoformat()
    doc={'order_id':f'KS-{datetime.now().year}-{secrets.randbelow(90000)+10000}','farmer_id':p['farmer_id'],'farmer_name':p.get('farmer_name','Farmer'),'buyer_id':user['id'],'buyer_name':user.get('business_name') or user['name'],'produce_id':data.produce_id,'product':p['crop'],'quantity':data.quantity,'price':p['expected_price'],'transport_cost':route['transport_cost'],'distance_km':route['distance_km'],'eta_min':route['duration_min'],'pickup_location':p['location'],'delivery_location':user.get('address') or 'Kolkata','pickup_lat':p_lat,'pickup_lon':p_lon,'delivery_lat':d_lat,'delivery_lon':d_lon,'status':'placed','created_at':now,'updated_at':now}
    result=await db.orders.insert_one(doc)
    await db.produce.update_one({'_id':ObjectId(data.produce_id)},{'$inc':{'quantity':-data.quantity}})
    await db.notifications.insert_one({'user_id':p['farmer_id'],'title':f"New order received: {data.quantity} {p.get('unit','kg')} {p['crop']} from {doc['buyer_name']}.",'kind':'order','read':False,'created_at':now})
    return clean(await db.orders.find_one({'_id':result.inserted_id}))

@api.get('/orders')
async def list_orders(user=Depends(current_user)):
    query={} if user['role']=='admin' else {'$or':[{'farmer_id':user['id']},{'buyer_id':user['id']}]}
    return [clean(o) for o in await db.orders.find(query).sort('created_at',-1).to_list(100)]

TRANSITIONS={'placed':['accepted','rejected'],'accepted':['preparing'],'preparing':['out_for_delivery'],'out_for_delivery':['delivered']}
STATUS_NOTICE={'accepted':'was accepted by','rejected':'was rejected by','preparing':'is being prepared by','out_for_delivery':'is out for delivery from','delivered':'was delivered from'}

@api.patch('/orders/{order_id}/status')
async def update_order(order_id: str, data: StatusInput, user=Depends(current_user)):
    order=await db.orders.find_one({'order_id':order_id})
    if not order: raise HTTPException(404,'Order not found.')
    if user['role']=='buyer': raise HTTPException(403,'Buyers cannot change the order status.')
    if user['role']=='farmer' and order['farmer_id']!=user['id']: raise HTTPException(403,'This order belongs to another farmer.')
    if data.status not in TRANSITIONS.get(order['status'],[]) and user['role']!='admin':
        raise HTTPException(400,f"An order that is {order['status'].replace('_',' ')} cannot move to {data.status.replace('_',' ')}.")
    now=datetime.now(timezone.utc).isoformat()
    result=await db.orders.find_one_and_update({'order_id':order_id},{'$set':{'status':data.status,'updated_at':now}},return_document=ReturnDocument.AFTER)
    if data.status=='rejected':
        from bson import ObjectId
        try: await db.produce.update_one({'_id':ObjectId(order['produce_id'])},{'$inc':{'quantity':order['quantity']}})
        except Exception: pass
    notice=STATUS_NOTICE.get(data.status)
    if notice:
        await db.notifications.insert_one({'user_id':order['buyer_id'],'title':f"Your order {order_id} ({order['quantity']} kg {order['product']}) {notice} {order.get('farmer_name','the farmer')}.",'kind':'order','read':False,'created_at':now})
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
    await db.meta.delete_many({'key':'seed_version'})
    await seed_demo(); await ensure_geo(); return {'message':'Demo data restored'}

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