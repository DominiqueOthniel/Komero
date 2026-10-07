from fastapi import APIRouter

from app.api.v1 import auth, dashboard, products, public, receipts_public, sales, stores, whatsapp

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(stores.router)
api_router.include_router(products.router)
api_router.include_router(sales.router)
api_router.include_router(dashboard.router)
api_router.include_router(public.router)
api_router.include_router(receipts_public.router)
api_router.include_router(whatsapp.router)
