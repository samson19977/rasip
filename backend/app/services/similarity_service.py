"""
Similarity Service v2 — pure Python, no numpy.
Cosine similarity across 11 district features.
"""
import math
from typing import List, Dict, Any

SOIL_CODES = {"Andosol": 5, "Cambisol": 4, "Ferralsol": 3, "Lixisol": 2, "Vertisol": 1}
FEATURE_RANGES = {
    "rainfall_annual_mm":  (700,  1800),
    "temp_mean_c":         (14,   23),
    "elevation_mean":      (1300, 2000),
    "soil_ph":             (4.5,  7.5),
    "humidity_pct":        (50,   85),
    "ndvi_mean":           (0.25, 0.70),
    "slope_mean":          (3,    20),
    "flood_risk_score":    (0,    70),
    "drought_risk_score":  (0,    75),
    "avg_maize_yield":     (2,    5),
    "avg_potato_yield":    (7,    22),
}
FEATURES = list(FEATURE_RANGES.keys())


def _norm_val(val, feat):
    lo, hi = FEATURE_RANGES.get(feat, (0, 1))
    if hi == lo:
        return 0.5
    return max(0.0, min(1.0, ((val or 0) - lo) / (hi - lo)))


def _to_vec(district):
    vals = [_norm_val(getattr(district, f, None), f) for f in FEATURES]
    vals.append(SOIL_CODES.get(district.soil_type or "", 0) / 5.0)
    return vals


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _magnitude(v):
    return math.sqrt(sum(x * x for x in v))


def _cosine(a, b):
    na, nb = _magnitude(a), _magnitude(b)
    return _dot(a, b) / (na * nb) if na and nb else 0.0


def _euclidean(a, b):
    dist = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
    return max(0.0, 1.0 - dist / math.sqrt(len(a)))


def _pearson(a, b):
    n = len(a)
    mean_a = sum(a) / n
    mean_b = sum(b) / n
    num    = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    den_a  = math.sqrt(sum((x - mean_a) ** 2 for x in a))
    den_b  = math.sqrt(sum((y - mean_b) ** 2 for y in b))
    return num / (den_a * den_b) if den_a and den_b else 0.0


class SimilarityService:

    async def find_similar(self, source, candidates: List, top_n=5, method="cosine", crop=None):
        sv      = _to_vec(source)
        scorer  = {"cosine": _cosine, "euclidean": _euclidean, "pearson": _pearson}.get(method, _cosine)
        results = []

        for d in candidates:
            if d.id == source.id:
                continue
            score   = scorer(sv, _to_vec(d))
            deltas  = {}
            for f in ["rainfall_annual_mm", "temp_mean_c", "soil_ph", "ndvi_mean", "humidity_pct"]:
                sv_val = getattr(source, f, 0) or 0
                dv_val = getattr(d, f, 0) or 0
                if sv_val:
                    deltas[f] = round(((dv_val - sv_val) / sv_val) * 100, 1)

            sim_pct = round(score * 100, 1)
            if sim_pct > 90:
                use_case = f"{source.name} and {d.name} are near-identical — {crop or 'maize'} strategies transfer directly."
            elif sim_pct > 75:
                use_case = f"{d.name} is highly similar to {source.name} — {crop or 'maize'} best practices likely transferable."
            else:
                use_case = f"{d.name} is moderately similar to {source.name} — adapt {crop or 'maize'} recommendations for local differences."

            results.append({
                "district_id":      d.id,
                "district_name":    d.name,
                "province":         d.province,
                "similarity_score": sim_pct,
                "similarity_pct":   f"{sim_pct}%",
                "elevation_m":      d.elevation_mean,
                "rainfall_mm":      d.rainfall_annual_mm,
                "temp_c":           d.temp_mean_c,
                "soil_type":        d.soil_type,
                "soil_ph":          d.soil_ph,
                "ndvi":             d.ndvi_mean,
                "humidity_pct":     d.humidity_pct,
                "flood_risk":       d.flood_risk_score,
                "feature_deltas":   deltas,
                "use_case":         use_case,
            })

        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_n]

    async def build_matrix(self, districts: List):
        vecs  = [_to_vec(d) for d in districts]
        names = [d.name for d in districts]
        n     = len(vecs)
        matrix = [[round(_cosine(vecs[i], vecs[j]) * 100, 1) for j in range(n)] for i in range(n)]
        return {"districts": names, "matrix": matrix}
