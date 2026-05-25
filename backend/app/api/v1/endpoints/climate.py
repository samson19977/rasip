from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.db_models import District, ClimateRecord
router = APIRouter()

@router.get("/risk/{district_id}")
async def climate_risk(district_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(District).where(District.id == district_id))
    d = r.scalar_one_or_none()
    if not d: raise HTTPException(404, "District not found")
    avg = ((d.flood_risk_score or 0) + (d.drought_risk_score or 0) + (d.soil_degradation_score or 0)) / 3
    overall = "High" if avg >= 55 else "Medium" if avg >= 35 else "Low"
    ndvi_status = ("Healthy" if (d.ndvi_mean or 0) >= 0.5 else "Moderate" if (d.ndvi_mean or 0) >= 0.35 else "Degraded")
    if (d.ndvi_trend or 0) > 0.01: ndvi_status += " (improving)"
    elif (d.ndvi_trend or 0) < -0.01: ndvi_status += " (declining)"
    recs = []
    if (d.flood_risk_score or 0) >= 50: recs.append("⚠️ High flood risk — avoid valley bottoms; improve drainage.")
    if (d.drought_risk_score or 0) >= 50: recs.append("⚠️ High drought risk — implement water harvesting; use drought-tolerant varieties.")
    if (d.soil_degradation_score or 0) >= 50: recs.append("⚠️ Soil degradation — apply organic mulch; practice contour farming.")
    if (d.ndvi_trend or 0) < -0.02: recs.append("📉 NDVI declining — investigate land use changes.")
    if not recs: recs.append("✅ Climate conditions within normal range.")
    return {"district": d.name, "province": d.province, "flood_risk_score": d.flood_risk_score,
            "drought_risk_score": d.drought_risk_score, "soil_degradation_score": d.soil_degradation_score,
            "overall_risk": overall, "ndvi_trend": d.ndvi_trend, "ndvi_status": ndvi_status, "recommendations": recs}

@router.get("/history/{district_id}")
async def climate_history(district_id: int, year: int = Query(None), db: AsyncSession = Depends(get_db)):
    stmt = select(ClimateRecord).where(ClimateRecord.district_id == district_id).order_by(ClimateRecord.year, ClimateRecord.month)
    if year: stmt = stmt.where(ClimateRecord.year == year)
    r = await db.execute(stmt)
    return [{"year": c.year, "month": c.month, "rainfall_mm": c.rainfall_mm, "temp_mean_c": c.temp_mean_c,
             "humidity_pct": c.humidity_pct, "ndvi": c.ndvi, "drought_score": c.drought_score,
             "flood_risk_score": c.flood_risk_score} for c in r.scalars().all()]

@router.get("/all-risks")
async def all_risks(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(District).order_by(District.name))
    return [{"id": d.id, "name": d.name, "province": d.province, "lat": d.centroid_lat, "lon": d.centroid_lon,
             "flood_risk": d.flood_risk_score, "drought_risk": d.drought_risk_score,
             "ndvi": d.ndvi_mean, "ndvi_trend": d.ndvi_trend} for d in r.scalars().all()]
