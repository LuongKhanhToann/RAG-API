from fastapi import APIRouter
from routes.process import router_process
from routes.search import router_search

api_router = APIRouter()

api_router.include_router(router_process, tags=["Process"])
api_router.include_router(router_search, tags=["Search"])