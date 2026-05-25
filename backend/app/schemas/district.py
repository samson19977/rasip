"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel
from typing import Optional

class DistrictBase(BaseModel):
    name: str
    province: str
    centroid_lat: Optional[float] = None
    centroid_lon: Optional[float] = None

class DistrictResponse(DistrictBase):
    id: int
    elevation_mean: Optional[float] = None
    rainfall_annual_mm: Optional[float] = None
    temp_mean_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    soil_type: Optional[str] = None
    soil_ph: Optional[float] = None
    ndvi_mean: Optional[float] = None
    flood_risk_score: Optional[float] = None
    drought_risk_score: Optional[float] = None
    class Config:
        from_attributes = True

class SuitabilityRequest(BaseModel):
    district_id: int
    crop: str
    variety: Optional[str] = None

class SuitabilityResponse(BaseModel):
    district_id: int
    district_name: str
    crop: str
    variety: Optional[str]
    suitability_score: float
    yield_prediction_t_ha: float
    risk_level: str
    confidence: float
    recommendation: str
    shap_values: dict
    feature_scores: dict
    top_positive_factors: list
    top_negative_factors: list
