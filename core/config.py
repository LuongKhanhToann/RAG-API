import os

backend_cors_origins = os.environ.get("BACKEND_CORS_ORIGINS")
db_name = os.environ.get("COLLECTION_NAME")
project_name = os.environ.get("PROJECT_NAME")
api_key = os.environ.get("API_KEY")
api_v1_str = "/ai"