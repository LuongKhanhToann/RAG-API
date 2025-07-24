import os

backend_cors_origins = os.getenv("BACKEND_CORS_ORIGINS")
db_name = os.getenv("COLLECTION_NAME", "RAG DB") 
project_name = os.getenv("PROJECT_NAME", "RAG API")  # default fallback
api_key = os.getenv("API_KEY")
api_embedded_key = os.getenv("API_EMBEDDED_KEY")
api_v1_str = "/ai"