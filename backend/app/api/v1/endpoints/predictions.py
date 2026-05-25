from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.db.database import get_db
from app.models.db_models import District, Prediction
from app.services.ml_service import MLService
router = APIRouter()
ml = MLService()

class SuitabilityRequest(BaseModel):
    district_id: int; crop: str; variety: Optional[str] = None

class YieldRequest(BaseModel):
    district_id: int; crop: str; rainfall_mm: Optional[float] = None

async def _get(district_id, db):
    r = await db.execute(select(District).where(District.id == district_id))
    d = r.scalar_one_or_none()
    if not d: raise HTTPException(404, "District not found")
    return d

@router.post("/suitability")
async def predict_suitability(req: SuitabilityRequest, db: AsyncSession = Depends(get_db)):
    district = await _get(req.district_id, db)
    result = await ml.predict_suitability(district, req.crop, req.variety)
    db.add(Prediction(district_id=district.id, crop=req.crop, variety=req.variety,
                      suitability_score=result["suitability_score"], yield_prediction_t_ha=result["yield_prediction_t_ha"],
                      risk_level=result["risk_level"], confidence=result["confidence"],
                      shap_values_json=result["shap_values"], recommendation=result["recommendation"]))
    await db.commit()
    return {"district_id": district.id, "district_name": district.name, **result}

@router.post("/yield")
async def predict_yield(req: YieldRequest, db: AsyncSession = Depends(get_db)):
    district = await _get(req.district_id, db)
    result = await ml.predict_yield(district, req)
    return {"district_id": district.id, **result}

@router.get("/history/{district_id}")
async def prediction_history(district_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Prediction).where(Prediction.district_id == district_id).order_by(Prediction.created_at.desc()).limit(50))
    return [{"id": p.id, "crop": p.crop, "variety": p.variety, "suitability_score": p.suitability_score,
             "yield_prediction_t_ha": p.yield_prediction_t_ha, "risk_level": p.risk_level, "created_at": str(p.created_at)}
            for p in r.scalars().all()]

@router.get("/crops")
async def list_crops(): return {"crops": ml.get_supported_crops()}

@router.get("/varieties/{crop}")
async def list_varieties(crop: str): return {"crop": crop, "varieties": ml.get_varieties(crop)}
