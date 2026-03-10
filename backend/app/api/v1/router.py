from fastapi import APIRouter

from app.api.v1.endpoints import cases

api_router = APIRouter()

api_router.include_router(cases.router)
