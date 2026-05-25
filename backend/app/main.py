from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.v1.endpoints import districts, predictions, similarity, climate, forecast, models
from app.db.database import init_db
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="RASIP — Rwanda Agricultural Spatial Intelligence Platform",
    description="AI-powered crop suitability, yield prediction, district similarity, and climate forecasting.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,   # uses the property
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(districts.router,   prefix="/api/v1/districts",   tags=["Districts"])
app.include_router(predictions.router, prefix="/api/v1/predict",     tags=["Predictions"])
app.include_router(similarity.router,  prefix="/api/v1/similarity",  tags=["Similarity"])
app.include_router(climate.router,     prefix="/api/v1/climate",     tags=["Climate"])
app.include_router(forecast.router,    prefix="/api/v1/forecast",    tags=["Forecast"])
app.include_router(models.router,      prefix="/api/v1/models",      tags=["Models"])


@app.get("/health")
async def health():
    return {"status": "ok", "platform": "RASIP", "version": "2.0.0"}


@app.get("/")
async def root():
    return {"name": "RASIP", "version": "2.0.0", "docs": "/docs"}
