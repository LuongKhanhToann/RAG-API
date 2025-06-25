from fastapi import APIRouter
from routes.process import router_process

api_router = APIRouter()

api_router.include_router(router_process, tags=["Process"])