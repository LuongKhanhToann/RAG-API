import os
from env import client
from qdrant_client.models import PointStruct, VectorParams, Distance
from schemas.message_common_schema import MessageCommon
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.function import embedding_model, gemini_model
from core.config import db_name
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    PDFMinerLoader
)
from fastapi import UploadFile
from typing import List
from langchain_core.documents import Document
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from langchain_core.documents import Document
import shutil
import uuid
import re
import fitz 
from PIL import Image
import io
import easyocr
import numpy as np
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

reader = easyocr.Reader(['en', 'vi']) 

SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
TEMP_DIR = "./temp_files"

def add_to_qdrant(chunks):
    if not client.collection_exists(db_name):
        client.recreate_collection(
            collection_name=db_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )
    
    points = []
    for doc in chunks:
        vector = embedding_model().encode(doc.page_content)
        # vector = embedding_model(doc.page_content)  
        point_id = str(uuid.uuid4())
        title = doc.metadata.get("title", "Untitled")
        source = doc.metadata.get("source", "")
        points.append(
            PointStruct(
                id=point_id,
                vector=vector.tolist(),
                payload={
                    "text": doc.page_content,
                    "source": source,
                    "title": title
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

def extract_google_doc_id(link_or_id: str) -> str:
    """
    Extract Google Docs ID from URL or return ID if acceptable formmat.
    """
    pattern = r"/d/([a-zA-Z0-9-_]+)"
    match = re.search(pattern, link_or_id)
    if match:
        return match.group(1)
    return link_or_id

def get_google_docs_service():
    creds = None
    token_path = 'token.json'
    creds_path = 'credentials.json'  #file OAuth

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    service = build('docs', 'v1', credentials=creds)
    return service

def load_google_doc(document_id: str) -> Document:
    service = get_google_docs_service()
    doc = service.documents().get(documentId=document_id).execute()
    content = doc.get('body', {}).get('content', [])

    full_text = ""
    for elem in content:
        if 'paragraph' in elem:
            elements = elem['paragraph'].get('elements', [])
            for e in elements:
                text_run = e.get('textRun')
                if text_run:
                    full_text += text_run.get('content', '')

    return Document(page_content=full_text, metadata={"source": f"GoogleDoc:{document_id}"})

def ocr_pdf_to_documents(file_path: str) -> List[Document]:
    doc = fitz.open(file_path)
    documents = []
    logger.debug(f"Total pages in PDF: {len(doc)}")
    
    source = f"OCR_PDF:{os.path.basename(file_path)}"
    
    for i, page in enumerate(doc):
        logger.debug(f"Processing page {i + 1} - Text: {page.get_text()[:100]}") 
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        img_np = np.array(img)

        text = reader.readtext(img_np, detail=0, paragraph=True)
        combined_text = "\n".join(text)

        if combined_text.strip():
            documents.append(Document(
                page_content=combined_text,
                metadata={"page": i + 1, "source": source}
            ))
        else:
            logger.debug(f"No text found on page {i + 1}.")
            
    if not documents:
        logger.debug("OCR returned no documents.")
    return documents

def load_document(file_path: str) -> List[Document]:
    if file_path.endswith(".pdf"):
        loader = PDFMinerLoader(file_path)
        docs = loader.load()
        logger.debug(f"Docs loaded: {docs}")
        if not docs or all(doc.page_content.strip() == "" for doc in docs):
            doc = fitz.open(file_path)
            docs = ocr_pdf_to_documents(file_path)
        if not docs:
            raise ValueError(f"No extractable content found in PDF: {file_path}")
        
    elif file_path.endswith(".docx"):
        loader = Docx2txtLoader(file_path)
        docs = loader.load()
    elif file_path.endswith(".txt"):
        loader = TextLoader(file_path, encoding="utf-8")
        docs = loader.load()
    else:
        raise ValueError("Unsupported file format.")
    return docs

def split_documents(documents: List[Document]) -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=300
    )
    return text_splitter.split_documents(documents)

def generate_title(text: str) -> str:
    prompt = f"""Read the following text and generate a short, meaningful title (max 10 words) that summarizes the main topic:

{text}

Title:"""
    try:
        response = gemini_model.generate_content(prompt)
        title = response.text.strip().replace('"', '')  # clean quotes

        if title:
            logger.debug(f"[TITLE_GEN] Title generated: {title}")
            return title
        else:
            logger.debug("[TITLE_GEN] Empty title generated, using 'Untitled'")
            return "Untitled"
    except Exception as e:
        logger.error(f"[TITLE_GEN] Failed to generate title: {e}")
        return "Untitled"

async def process_data(file: UploadFile = None, google_doc_id: str = None) -> MessageCommon:
    try:
        if google_doc_id:
            doc_id = extract_google_doc_id(google_doc_id)
            document = load_google_doc(doc_id)
            chunks = split_documents([document])
        elif file and file != None:
            file_path = save_uploaded_file(file)
            documents = load_document(file_path)
            chunks = split_documents(documents)
            os.remove(file_path)
        else:
            return MessageCommon(detail="No input provided.")
        if chunks:
            for chunk in chunks:
                title = generate_title(chunk.page_content)
                chunk.metadata["title"] = title
        add_to_qdrant(chunks)
        return MessageCommon(detail="Data updated successfully.")

    except Exception as e:
        return MessageCommon(detail=f"Processing failed: {str(e)}")
