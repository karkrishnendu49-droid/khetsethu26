import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]

def clean(doc):
    if not doc: return None
    doc = dict(doc)
    if '_id' in doc: doc['id'] = str(doc.pop('_id'))
    for key, value in list(doc.items()):
        if hasattr(value, 'isoformat'): doc[key] = value.isoformat()
    return doc
