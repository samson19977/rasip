from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.db_models import District
router = APIRouter()

def _s(d):
    return {"id": d.id, "name": d.name, "province": d.province, "centroid_lat": d.centroid_lat,
            "centroid_lon": d.centroid_lon, "elevation_mean": d.elevation_mean, "area_km2": d.area_km2,
            "rainfall_annual_mm": d.rainfall_annual_mm, "temp_mean_c": d.temp_mean_c,
            "humidity_pct": d.humidity_pct, "soil_type": d.soil_type, "soil_ph": d.soil_ph,
            "ndvi_mean": d.ndvi_mean, "ndvi_trend": d.ndvi_trend, "flood_risk_score": d.flood_risk_score,
            "drought_risk_score": d.drought_risk_score, "soil_degradation_score": d.soil_degradation_score,
            "avg_maize_yield": d.avg_maize_yield, "avg_potato_yield": d.avg_potato_yield,
            "avg_coffee_yield": d.avg_coffee_yield, "avg_tea_yield": d.avg_tea_yield,
            "coffee_suitable": d.coffee_suitable, "tea_suitable": d.tea_suitable, "banana_suitable": d.banana_suitable}

@router.get("/")
async def list_districts(province: str = Query(None), db: AsyncSession = Depends(get_db)):
    stmt = select(District).order_by(District.province, District.name)
    if province: stmt = stmt.where(District.province == province)
    result = await db.execute(stmt)
    return [_s(d) for d in result.scalars().all()]

@router.get("/{district_id}")
async def get_district(district_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(District).where(District.id == district_id))
    d = result.scalar_one_or_none()
    if not d: raise HTTPException(status_code=404, detail="District not found")
    return _s(d)
