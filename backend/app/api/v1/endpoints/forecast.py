from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.db_models import District
from app.services.forecast_service import ForecastService
router = APIRouter()
svc = ForecastService()

@router.get("/{district_id}")
async def forecast_climate(district_id: int, months: int = Query(12, ge=1, le=24), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(District).where(District.id == district_id))
    d = r.scalar_one_or_none()
    if not d: raise HTTPException(404, "District not found")
    return {"district": d.name, "province": d.province, "months_forecast": months,
            "drought_warning": svc.get_drought_early_warning(d),
            "forecasts": svc.forecast_district(d, months_ahead=months)}

@router.get("/warning/{district_id}")
async def drought_warning(district_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(District).where(District.id == district_id))
    d = r.scalar_one_or_none()
    if not d: raise HTTPException(404, "District not found")
    return svc.get_drought_early_warning(d)
