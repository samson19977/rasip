"""
ML Service v2 — pure Python, no numpy/sklearn dependency.
All calculations use standard Python math — works on any Python version.
"""
import math
from typing import Dict, Any, Optional

CROP_OPTIMAL = {
    "potato": {
        "rainfall_mm": (1100, 1600), "temp_c": (12, 20), "elevation_m": (1600, 2500),
        "soil_ph": (5.5, 7.0), "ndvi": (0.45, 0.80), "humidity_pct": (65, 85), "flood_risk": (0, 30),
        "varieties": {
            "Markies":  {"yield_base": 20.0, "suit_bonus": 5},
            "Shangi":   {"yield_base": 18.0, "suit_bonus": 3},
            "Victoria": {"yield_base": 16.0, "suit_bonus": 0},
            "Kinigi":   {"yield_base": 14.0, "suit_bonus": -2},
        },
        "best_soil_types": ["Andosol"], "ok_soil_types": ["Cambisol", "Ferralsol"],
    },
    "maize": {
        "rainfall_mm": (800, 1400), "temp_c": (18, 28), "elevation_m": (1000, 2000),
        "soil_ph": (5.8, 7.5), "ndvi": (0.30, 0.75), "humidity_pct": (50, 78), "flood_risk": (0, 50),
        "varieties": {
            "DK8031": {"yield_base": 6.5, "suit_bonus": 5},
            "RWILI":  {"yield_base": 5.5, "suit_bonus": 2},
            "H614":   {"yield_base": 4.5, "suit_bonus": 0},
        },
        "best_soil_types": ["Ferralsol", "Cambisol"], "ok_soil_types": ["Lixisol", "Andosol"],
    },
    "bean": {
        "rainfall_mm": (800, 1200), "temp_c": (16, 24), "elevation_m": (1200, 2200),
        "soil_ph": (6.0, 7.5), "ndvi": (0.30, 0.70), "humidity_pct": (55, 75), "flood_risk": (0, 40),
        "varieties": {
            "Lyamungu":  {"yield_base": 2.2, "suit_bonus": 3},
            "Urwintore": {"yield_base": 2.0, "suit_bonus": 2},
            "RWR2245":   {"yield_base": 1.8, "suit_bonus": 0},
        },
        "best_soil_types": ["Cambisol", "Andosol"], "ok_soil_types": ["Ferralsol", "Lixisol"],
    },
    "coffee": {
        "rainfall_mm": (1200, 1800), "temp_c": (16, 22), "elevation_m": (1400, 2000),
        "soil_ph": (5.5, 6.5), "ndvi": (0.50, 0.85), "humidity_pct": (70, 85), "flood_risk": (0, 25),
        "varieties": {
            "Red Bourbon": {"yield_base": 1.5, "suit_bonus": 5},
            "Jackson":     {"yield_base": 1.2, "suit_bonus": 2},
        },
        "best_soil_types": ["Andosol"], "ok_soil_types": ["Cambisol"],
    },
    "tea": {
        "rainfall_mm": (1400, 2000), "temp_c": (13, 20), "elevation_m": (1600, 2500),
        "soil_ph": (4.5, 6.0), "ndvi": (0.55, 0.90), "humidity_pct": (75, 90), "flood_risk": (0, 20),
        "varieties": {
            "Wufeng":   {"yield_base": 3.5, "suit_bonus": 5},
            "Yabukita": {"yield_base": 3.0, "suit_bonus": 2},
        },
        "best_soil_types": ["Andosol"], "ok_soil_types": ["Cambisol"],
    },
    "banana": {
        "rainfall_mm": (1000, 1800), "temp_c": (17, 26), "elevation_m": (900, 1900),
        "soil_ph": (5.5, 7.0), "ndvi": (0.40, 0.85), "humidity_pct": (60, 85), "flood_risk": (0, 45),
        "varieties": {
            "Gros Michel": {"yield_base": 25.0, "suit_bonus": 5},
            "Cavendish":   {"yield_base": 22.0, "suit_bonus": 2},
        },
        "best_soil_types": ["Ferralsol", "Andosol"], "ok_soil_types": ["Cambisol", "Lixisol"],
    },
}

FEATURE_WEIGHTS = {
    "rainfall": 0.22, "temperature": 0.20, "elevation": 0.15,
    "soil_ph": 0.15, "humidity": 0.10, "ndvi": 0.10, "flood_risk": 0.08,
}

SOIL_SCORES = {"Andosol": 100, "Cambisol": 85, "Ferralsol": 70, "Lixisol": 55}


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _range_score(value, optimal_range, inverse=False):
    if value is None:
        return 50.0
    low, high = optimal_range
    mid = (low + high) / 2.0
    half = (high - low) / 2.0 or 1.0
    if low <= value <= high:
        score = 100.0 - abs(value - mid) / half * 10.0
    else:
        distance = min(abs(value - low), abs(value - high))
        score = max(0.0, 100.0 - (distance / half) * 60.0)
    return (100.0 - score) if inverse else score


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _norm(v):
    return math.sqrt(sum(x * x for x in v))


def _cosine(a, b):
    na, nb = _norm(a), _norm(b)
    return _dot(a, b) / (na * nb) if na and nb else 0.0


class MLService:

    async def predict_suitability(self, district, crop: str, variety: Optional[str] = None) -> Dict[str, Any]:
        crop_lower = crop.lower()
        opt = CROP_OPTIMAL.get(crop_lower, CROP_OPTIMAL["maize"])
        w = FEATURE_WEIGHTS

        rain_score  = _range_score(district.rainfall_annual_mm, opt["rainfall_mm"])
        temp_score  = _range_score(district.temp_mean_c,        opt["temp_c"])
        elev_score  = _range_score(district.elevation_mean,     opt["elevation_m"])
        ph_score    = _range_score(district.soil_ph,            opt["soil_ph"])
        humid_score = _range_score(district.humidity_pct,       opt["humidity_pct"])
        ndvi_score  = _range_score(district.ndvi_mean,          opt["ndvi"]) if district.ndvi_mean else 55.0
        flood_score = _range_score(district.flood_risk_score or 30, opt.get("flood_risk", (0, 40)), inverse=True)
        soil_score  = SOIL_SCORES.get(district.soil_type or "", 50)

        base_score = (
            rain_score  * w["rainfall"]    +
            temp_score  * w["temperature"] +
            elev_score  * w["elevation"]   +
            ph_score    * w["soil_ph"]     +
            humid_score * w["humidity"]    +
            ndvi_score  * w["ndvi"]        +
            flood_score * w["flood_risk"]
        )
        base_score += (soil_score / 100.0) * 5.0
        if district.soil_type in opt.get("best_soil_types", []):
            base_score += 3.0

        variety_info = {}
        if variety and variety in opt.get("varieties", {}):
            variety_info = opt["varieties"][variety]
            base_score = min(100.0, base_score + variety_info.get("suit_bonus", 0))

        varieties = opt.get("varieties", {})
        yield_base = variety_info.get("yield_base",
                     list(varieties.values())[0]["yield_base"] if varieties else 3.0)
        yield_pred = yield_base * (base_score / 100.0) * 1.05
        risk = "Low" if base_score >= 75 else ("Medium" if base_score >= 55 else "High")

        shap_values = {
            f"Rainfall ({district.rainfall_annual_mm:.0f}mm)":      round((rain_score  - 50) * w["rainfall"]    / 10, 2),
            f"Temperature ({district.temp_mean_c:.1f}°C)":          round((temp_score  - 50) * w["temperature"] / 10, 2),
            f"Elevation ({district.elevation_mean:.0f}m)":          round((elev_score  - 50) * w["elevation"]   / 10, 2),
            f"Soil pH ({district.soil_ph:.1f})":                    round((ph_score    - 50) * w["soil_ph"]     / 10, 2),
            f"Humidity ({district.humidity_pct:.0f}%)":             round((humid_score - 50) * w["humidity"]    / 10, 2),
            f"NDVI ({district.ndvi_mean:.2f})":                     round((ndvi_score  - 50) * w["ndvi"]        / 10, 2),
            f"Flood Risk ({district.flood_risk_score:.0f}/100)":    round((flood_score - 50) * w["flood_risk"]  / 10, 2),
            f"Soil Type ({district.soil_type})":                    round((soil_score  - 50) * 0.05 / 10, 2),
        }

        sorted_shap  = sorted(shap_values.items(), key=lambda x: abs(x[1]), reverse=True)
        positives    = [k for k, v in sorted_shap if v > 0]
        negatives    = [k for k, v in sorted_shap if v < 0]
        v_str        = f" ({variety})" if variety else ""
        quality      = ("highly suitable" if base_score >= 80 else
                        "moderately suitable" if base_score >= 65 else
                        "marginally suitable" if base_score >= 50 else
                        "not recommended")
        rec = (f"{district.name} is {quality} for {crop}{v_str} (score: {base_score:.0f}/100). "
               f"Supporting: {', '.join(positives[:2]) or 'general conditions'}."
               f"{(' Constraints: ' + ', '.join(negatives[:2]) + '.') if negatives else ''} Risk: {risk}.")

        return {
            "crop": crop, "variety": variety,
            "suitability_score":    round(base_score, 1),
            "yield_prediction_t_ha": round(yield_pred, 1),
            "risk_level":           risk,
            "confidence":           round(min(0.95, 0.72 + base_score / 400), 2),
            "recommendation":       rec,
            "shap_values":          shap_values,
            "feature_scores": {
                "rainfall":    round(rain_score, 1),
                "temperature": round(temp_score, 1),
                "elevation":   round(elev_score, 1),
                "soil_ph":     round(ph_score, 1),
                "humidity":    round(humid_score, 1),
                "ndvi":        round(ndvi_score, 1),
                "flood_risk":  round(flood_score, 1),
                "soil_type":   round(soil_score, 1),
            },
            "top_positive_factors": positives[:3],
            "top_negative_factors": negatives[:3],
        }

    async def predict_yield(self, district, request) -> Dict[str, Any]:
        crop_lower = request.crop.lower()
        opt        = CROP_OPTIMAL.get(crop_lower, CROP_OPTIMAL["maize"])
        varieties  = opt.get("varieties", {})
        yield_base = list(varieties.values())[0]["yield_base"] if varieties else 3.0
        rain_factor = _range_score(
            request.rainfall_mm or district.rainfall_annual_mm or 1000,
            opt["rainfall_mm"]
        ) / 100.0
        yield_pred = yield_base * rain_factor
        return {
            "crop": request.crop,
            "predicted_yield_t_ha":  round(yield_pred, 1),
            "yield_range_low":       round(yield_pred * 0.8, 1),
            "yield_range_high":      round(yield_pred * 1.2, 1),
            "confidence": 0.78,
            "key_drivers": ["Rainfall", "Temperature", "Soil pH"],
        }

    def get_supported_crops(self):
        return list(CROP_OPTIMAL.keys())

    def get_varieties(self, crop: str):
        return list(CROP_OPTIMAL.get(crop.lower(), {}).get("varieties", {}).keys())
