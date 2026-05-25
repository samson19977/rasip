from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.db_models import District
from app.services.similarity_service import SimilarityService
router = APIRouter()
svc = SimilarityService()

@router.get("/{district_id}")
async def find_similar(district_id: int, top_n: int = Query(5, ge=1, le=20),
                       method: str = Query("cosine"), crop: str = Query(None),
                       db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(District).where(District.id == district_id))
    source = r.scalar_one_or_none()
    if not source: raise HTTPException(404, "District not found")
    all_r = await db.execute(select(District))
    candidates = all_r.scalars().all()
    similar = await svc.find_similar(source, candidates, top_n=top_n, method=method, crop=crop)
    return {"source_district": source.name, "method": method, "crop": crop, "similar_districts": similar}

@router.get("/matrix/all")
async def similarity_matrix(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(District).order_by(District.name))
    return await svc.build_matrix(r.scalars().all())
