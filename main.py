from fastapi import FastAPI
from core.config import project_name, api_v1_str, backend_cors_origins
from starlette.middleware.cors import CORSMiddleware
from routes.main import api_router

app = FastAPI(
    title=project_name,
    openapi_url=f"{api_v1_str}/openapi.json",
)

# Set all CORS enabled origins
if backend_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["x-file-name"],
    )

app.include_router(api_router, prefix=api_v1_str)