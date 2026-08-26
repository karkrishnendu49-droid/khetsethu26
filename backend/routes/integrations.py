from fastapi import APIRouter, Depends
from utils.auth import admin_only
from services.map_service import integration_status, test_service

router = APIRouter(prefix='/api')

@router.get('/admin/integrations')
async def integrations(user=Depends(admin_only)):
    return {'integrations': await integration_status()}

@router.post('/admin/integrations/test/{service}')
async def run_test(service: str, user=Depends(admin_only)):
    return await test_service(service)
