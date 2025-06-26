from fastapi import File, UploadFile
from fastapi import APIRouter
from schemas.message_common_schema import MessageCommon 
from repositories import process

router_process = APIRouter()

@router_process.post("/process")
async def process_data(file: UploadFile = File(...)) -> MessageCommon:
   return await process.process_data(file)