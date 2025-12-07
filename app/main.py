from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import get_settings
from .routers import auth_router, charts_router, templates_router, subscription_router
from .routers.ai import router as ai_router
from .routers.profile import router as profile_router
from .routers.payment import router as payment_router
from .routers.iap import router as iap_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("🚀 Graphzy API starting up...")
    yield
    # Shutdown
    print("👋 Graphzy API shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="Graphzy API",
    description="AI-powered chart and data visualization generator",
    version="1.0.0",
    lifespan=lifespan
)

# Get settings
settings = get_settings()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(charts_router)
app.include_router(templates_router)
app.include_router(subscription_router)
app.include_router(payment_router)
app.include_router(ai_router)
app.include_router(profile_router)
app.include_router(iap_router)


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "name": "Graphzy API",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

