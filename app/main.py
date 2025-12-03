from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.config import settings
from app.routers import collage
from app.models.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: Ensure directories exist
    settings.INPUTS_PATH.mkdir(parents=True, exist_ok=True)
    settings.OUTPUTS_PATH.mkdir(parents=True, exist_ok=True)
    settings.BORDERS_PATH.mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Collage Tool API",
    description="Product collage generator with background removal",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving uploads
if settings.UPLOADS_PATH.exists():
    app.mount("/static", StaticFiles(directory=str(settings.UPLOADS_PATH)), name="static")

# Include routers
app.include_router(collage.router)


@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    from sqlalchemy import text
    from app.db.database import SessionLocal

    # Check database
    db_status = "ok"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        db_status = f"error: {str(e)}"

    # Check storage
    storage_status = "ok"
    if not settings.STORAGE_PATH.exists():
        storage_status = "error: storage path not found"

    return HealthResponse(
        status="healthy" if db_status == "ok" and storage_status == "ok" else "unhealthy",
        database=db_status,
        storage=storage_status
    )


@app.get("/api/info")
async def api_info():
    """Get API configuration info."""
    return {
        "canvas_size": f"{settings.CANVAS_WIDTH}x{settings.CANVAS_HEIGHT}",
        "image1_ratio": settings.IMAGE1_WIDTH_RATIO,
        "image2_ratio": settings.IMAGE2_WIDTH_RATIO,
        "base_url": settings.BASE_URL,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
