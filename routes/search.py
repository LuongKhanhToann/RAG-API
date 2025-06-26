from fastapi import APIRouter
from schemas.message_common_schema import Response 
from repositories import search

router_search = APIRouter()

@router_search.post("/search")
def search_rag(query:str) -> Response:
   return search.search_rag(query)