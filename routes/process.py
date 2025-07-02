from fastapi import File, UploadFile, File, Form
from typing import Optional
from fastapi import APIRouter
from schemas.message_common_schema import MessageCommon 
from repositories import process

router_process = APIRouter()

@router_process.post("/process")
async def process_data(file: Optional[UploadFile] = File(None),google_doc_id: Optional[str] = Form(None)) -> MessageCommon:
   return await process.process_data(file=file, google_doc_id=google_doc_id)