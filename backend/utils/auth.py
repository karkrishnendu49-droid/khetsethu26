import os, jwt
from fastapi import HTTPException, Request, Depends
from bson import ObjectId
from utils.db import db, clean

SECRET = os.environ['JWT_SECRET']
ALGORITHM = 'HS256'

async def current_user(request: Request):
    raw = request.cookies.get('access_token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    if not raw: raise HTTPException(401, 'Please log in to continue.')
    try:
        payload = jwt.decode(raw, SECRET, algorithms=[ALGORITHM])
        if payload.get('type') != 'access': raise ValueError()
        user = await db.users.find_one({'_id': ObjectId(payload['sub'])}, {'password_hash': 0})
        if not user: raise ValueError()
        return clean(user)
    except HTTPException: raise
    except Exception: raise HTTPException(401, 'Your session has expired. Please log in again.')

async def admin_only(user=Depends(current_user)):
    if user['role'] != 'admin': raise HTTPException(403, 'Admin access required.')
    return user
