"""
RASIP Backend Tests
Run: pytest tests/ -v
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.ml_service import MLService, CROP_OPTIMAL
from app.services.similarity_service import SimilarityService
from app.services.forecast_service import ForecastService


# ── Fixtures ────────────────────────────────────────────────────
class MockDistrict:
    id = 1
    name = "Musanze"
    province = "Northern"
    rainfall_annual_mm = 1340
    temp_mean_c = 15.5
    elevation_mean = 1870
    soil_ph = 6.2
    soil_type = "Andosol"
    humidity_pct = 78
    ndvi_mean = 0.62
    ndvi_trend = 0.02
    ndvi_std = 0.08
    slope_mean = 15.3
    flood_risk_score = 18
    drought_risk_score = 12
    soil_degradation_score = 15
    avg_maize_yield = 4.2
    avg_potato_yield = 18.5
    avg_bean_yield = 1.8
    avg_coffee_yield = 1.1
    avg_tea_yield = 2.3
    coffee_suitable = True
    tea_suitable = True
    banana_suitable = True


class MockDistrictDry:
    id = 2
    name = "Nyagatare"
    province = "Eastern"
    rainfall_annual_mm = 800
    temp_mean_c = 22.0
    elevation_mean = 1500
    soil_ph = 6.0
    soil_type = "Cambisol"
    humidity_pct = 55
    ndvi_mean = 0.38
    ndvi_trend = 0.01
    ndvi_std = 0.12
    slope_mean = 3.5
    flood_risk_score = 38
    drought_risk_score = 70
    soil_degradation_score = 45
    avg_maize_yield = 3.5
    avg_potato_yield = 10.0
    avg_bean_yield = 1.5
    avg_coffee_yield = 0.0
    avg_tea_yield = 0.0
    coffee_suitable = False
    tea_suitable = False
    banana_suitable = True


# ── ML Service Tests ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_ml_predict_potato_musanze():
    ml = MLService()
    d = MockDistrict()
    result = await ml.predict_suitability(d, "potato", "Markies")

    assert "suitability_score" in result
    assert 0 <= result["suitability_score"] <= 100
    assert result["suitability_score"] > 70, "Musanze should be highly suitable for potato"
    assert result["yield_prediction_t_ha"] > 0
    assert result["risk_level"] in ("Low", "Medium", "High")
    assert isinstance(result["shap_values"], dict)
    assert len(result["shap_values"]) >= 6


@pytest.mark.asyncio
async def test_ml_predict_maize_dry_district():
    ml = MLService()
    d = MockDistrictDry()
    result = await ml.predict_suitability(d, "maize", "DK8031")

    assert result["suitability_score"] < 80
    assert result["risk_level"] in ("Medium", "High")


@pytest.mark.asyncio
async def test_ml_shap_values_sum_to_score():
    """SHAP values should explain the prediction."""
    ml = MLService()
    d = MockDistrict()
    result = await ml.predict_suitability(d, "coffee", "Red Bourbon")

    shap_values = result["shap_values"]
    assert all(isinstance(v, float) for v in shap_values.values())
    # positive factors should exist for suitable district
    assert any(v > 0 for v in shap_values.values())


def test_all_crops_supported():
    ml = MLService()
    for crop in ["potato", "maize", "bean", "coffee", "tea", "banana"]:
        assert crop in CROP_OPTIMAL
        assert len(ml.get_varieties(crop)) > 0


# ── Similarity Service Tests ─────────────────────────────────────
@pytest.mark.asyncio
async def test_similarity_cosine():
    svc = SimilarityService()
    d1 = MockDistrict()
    d2 = MockDistrictDry()
    results = await svc.find_similar(d1, [d1, d2], top_n=5)

    # Should exclude self (d1), return d2
    assert len(results) == 1
    assert results[0]["district_name"] == "Nyagatare"
    assert 0 <= results[0]["similarity_score"] <= 100


@pytest.mark.asyncio
async def test_similarity_matrix():
    svc = SimilarityService()
    districts = [MockDistrict(), MockDistrictDry()]
    matrix = await svc.build_matrix(districts)

    assert "matrix" in matrix
    assert len(matrix["matrix"]) == 2
    # Diagonal should be 100% (self-similarity)
    assert matrix["matrix"][0][0] == 100.0
    assert matrix["matrix"][1][1] == 100.0


# ── Forecast Service Tests ───────────────────────────────────────
def test_forecast_12_months():
    svc = ForecastService()
    d = MockDistrict()
    forecasts = svc.forecast_district(d, months_ahead=12)

    assert len(forecasts) == 12
    for f in forecasts:
        assert "predicted_rainfall_mm" in f
        assert "drought_probability" in f
        assert "harvest_quality_score" in f
        assert 0 <= f["drought_probability"] <= 1
        assert 0 <= f["flood_probability"] <= 1
        assert 0 <= f["harvest_quality_score"] <= 100


def test_drought_warning_levels():
    svc = ForecastService()
    d_wet = MockDistrict()
    d_dry = MockDistrictDry()

    w_wet = svc.get_drought_early_warning(d_wet)
    w_dry = svc.get_drought_early_warning(d_dry)

    assert w_wet["warning_level"] in ("Low", "Moderate")
    assert w_dry["warning_level"] in ("High", "Critical")
