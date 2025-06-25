
import os
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from schemas.message_common_schema import MessageCommon
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.function import embedding_model
from core.config import db_name
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader
)
from fastapi import UploadFile
from typing import List
from langchain_core.documents import Document
import shutil
import uuid

TEMP_DIR = "./temp_files"
client = QdrantClient("localhost", port=6333)

def add_to_qdrant(chunks):
    if not client.collection_exists(db_name):
        client.recreate_collection(
            collection_name=db_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )
    
    points = []
    for doc in chunks:
        vector = embedding_model().encode(doc.page_content)
        point_id = str(uuid.uuid4())
        points.append(
            PointStruct(
                id=point_id,
                vector=vector.tolist(),
                payload={
                    "text": doc.page_content,
                    "source": doc.metadata.get("source", "")
                }
            )
        )
    client.upsert(collection_name=db_name, points=points)

def save_uploaded_file(file: UploadFile) -> str:
    os.makedirs(TEMP_DIR, exist_ok=True)
    file_path = os.path.join(TEMP_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return file_path

def load_document(file_path: str) -> List[Document]:
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith(".docx"):
        loader = Docx2txtLoader(file_path)
    elif file_path.endswith(".txt"):
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        raise ValueError("Unsupported file format.")
    return loader.load()

def split_documents(documents: List[Document]) -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    return text_splitter.split_documents(documents)

async def process_data(file: UploadFile) -> MessageCommon:
    try:
        file_path = save_uploaded_file(file)
        documents = load_document(file_path)
        chunks = split_documents(documents)
        add_to_qdrant(chunks)
        os.remove(file_path)  # Xoá file tạm
        return MessageCommon(detail="Data updated successfully.")
    except Exception as e:
        return MessageCommon(detail=f"Processing failed: {str(e)}")
