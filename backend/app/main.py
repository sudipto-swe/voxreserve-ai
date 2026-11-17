from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api.endpoints import api_router
from app.websocket.conversation_socket import ws_router

# Initialize database schema tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="VOXRESERVE: Production Real-Time AI Restaurant Voice Agent Backend"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(ws_router)

@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "VOXRESERVE AI Restaurant Voice Agent",
        "version": "1.0.0"
    }
