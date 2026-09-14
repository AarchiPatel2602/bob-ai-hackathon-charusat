from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import engine, Base
import backend.app.models # Import all models to ensure metadata registration

# Include routers
from backend.app.api.auth import router as auth_router
from backend.app.api.shipments import router as shipments_router
from backend.app.api.disruptions import router as disruptions_router
from backend.app.api.fleet import router as fleet_router
from backend.app.api.alerts import router as alerts_router
from backend.app.api.sensors import router as sensors_router
from backend.app.api.recommendations import router as recommendations_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.ai import router as ai_router
from backend.app.api.demo import router as demo_router
from backend.app.api.mcp import router as mcp_router

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="RouteWise AI - L2 Supply Chain Disruption Assistant & Fleet Utilisation Optimizer"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers under /api
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(shipments_router, prefix=settings.API_V1_STR)
app.include_router(disruptions_router, prefix=settings.API_V1_STR)
app.include_router(fleet_router, prefix=settings.API_V1_STR)
app.include_router(alerts_router, prefix=settings.API_V1_STR)
app.include_router(sensors_router, prefix=settings.API_V1_STR)
app.include_router(recommendations_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(ai_router, prefix=settings.API_V1_STR)
app.include_router(demo_router, prefix=settings.API_V1_STR)
app.include_router(mcp_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
