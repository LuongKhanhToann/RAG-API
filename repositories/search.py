import google.generativeai as genai
from qdrant_client.http import models as rest
from langchain_core.documents import Document
from schemas.message_common_schema import MessageCommon, Response
from utils.function import embedding_model
from core.config import db_name,api_key
from env import client
import numpy as np

genai.configure(api_key=api_key)
gemini_model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")

def search_rag(query: str, top_k: int = 5) -> Response:
    try:
        query_vector = embedding_model().encode(query).tolist()

        search_result = client.search(
            collection_name=db_name,
            query_vector=query_vector,
            limit=top_k,
            search_params=rest.SearchParams(hnsw_ef=128)
        )

        retrieved_texts = [hit.payload["text"] for hit in search_result if "text" in hit.payload]
        sources = [hit.payload.get("source", "Không rõ nguồn") for hit in search_result]

        if not retrieved_texts:
            return Response(answer="Không tìm thấy dữ liệu phù hợp.", contexts=[], sources=[])

        context = "\n\n".join(retrieved_texts)
        prompt = f"""Dưới đây là các đoạn văn bản được trích xuất từ cơ sở dữ liệu:

{context}

Câu hỏi: {query}

Dựa trên nội dung trên, hãy trả lời câu hỏi một cách chính xác và đầy đủ."""

        response = gemini_model.generate_content(prompt)

        return Response(
            answer=response.text,
            contexts=retrieved_texts,
            sources=sources
        )

    except Exception as e:
        return Response(
            answer="Lỗi khi xử lý truy vấn.",
            contexts=[],
            sources=[str(e)]
        )
