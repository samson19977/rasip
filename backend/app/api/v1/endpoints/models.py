from fastapi import APIRouter
from app.services.ml_service import CROP_OPTIMAL, FEATURE_WEIGHTS
router = APIRouter()

@router.get("/")
async def list_models():
    return {"version": "2.0.0", "features": list(FEATURE_WEIGHTS.keys()),
            "feature_weights": FEATURE_WEIGHTS, "supported_crops": list(CROP_OPTIMAL.keys()),
            "similarity_methods": ["cosine", "euclidean", "pearson"], "explainability": "SHAP-style attribution"}

@router.get("/crops/{crop}")
async def crop_parameters(crop: str):
    params = CROP_OPTIMAL.get(crop.lower())
    if not params: return {"error": f"Crop '{crop}' not found"}
    return {"crop": crop, "optimal_parameters": {k: v for k, v in params.items() if k != "varieties"},
            "varieties": list(params.get("varieties", {}).keys())}
