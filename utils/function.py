from dotenv import load_dotenv
load_dotenv()
from sentence_transformers import SentenceTransformer   #HuggingFace Model 
from core.config import api_embedded_key
import google.generativeai as genai
from core.config import api_key
import openai
import os

def embedding_model():
    model = SentenceTransformer('paraphrase-mpnet-base-v2')
    return model

#Open AI
# openai.api_key = api_embedded_key
# def embedding_model(text: str) -> list:
#     response = openai.embeddings.create(
#         model="text-embedding-3-small",  
#         input=text
#     )
#     return response.data[0].embedding


#Gemini
# genai.configure(api_key=api_embedded_key)
# def embedding_model(text: str) -> list:
#     response = genai.embed_content(
#         model="models/embedding-gecko-001",
#         content=text,
#         task_type="retrieval_document"
#     )
#     return response['embedding']


#Gemini
genai.configure(api_key=api_key)
gemini_model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")

#OpenAI
# openai.api_key = api_key