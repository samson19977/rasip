"""District similarity service — cosine, euclidean, pearson using 11 features."""
import numpy as np
from typing import List, Dict, Any

SOIL_CODES = {"Andosol": 5, "Cambisol": 4, "Ferralsol": 3, "Lixisol": 2, "Vertisol": 1}
FEATURE_RANGES = {
    "rainfall_annual_mm": (700, 1800), "temp_mean_c": (14, 23),
    "elevation_mean": (1300, 2000), "soil_ph": (4.5, 7.5),
    "humidity_pct": (50, 85), "ndvi_mean": (0.25, 0.70),
    "slope_mean": (3, 20), "flood_risk_score": (0, 70),
    "drought_risk_score": (0, 75), "avg_maize_yield": (2, 5), "avg_potato_yield": (7, 22),
}
FEATURES = list(FEATURE_RANGES.keys())

class SimilarityService:
    def _norm(self, val, feat):
        lo, hi = FEATURE_RANGES.get(feat, (0, 1))
        if hi == lo: return 0.5
        return max(0.0, min(1.0, ((val or 0) - lo) / (hi - lo)))

    def _vec(self, d):
        vals = [self._norm(getattr(d, f, None), f) for f in FEATURES]
        vals.append(SOIL_CODES.get(d.soil_type or "", 0) / 5.0)
        return np.array(vals, dtype=float)

    def _cosine(self, a, b):
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        return float(np.dot(a, b) / (na * nb)) if na and nb else 0.0

    def _euclidean(self, a, b):
        return max(0.0, 1.0 - np.linalg.norm(a - b) / np.sqrt(len(a)))

    def _pearson(self, a, b):
        if np.std(a) == 0 or np.std(b) == 0: return 0.0
        return float(np.corrcoef(a, b)[0, 1])

    async def find_similar(self, source, candidates: List, top_n=5, method="cosine", crop=None):
        sv = self._vec(source)
        scorer = {"cosine": self._cosine, "euclidean": self._euclidean, "pearson": self._pearson}[method]
        results = []
        for d in candidates:
            if d.id == source.id: continue
            score = scorer(sv, self._vec(d))
            deltas = {}
            for f in ["rainfall_annual_mm", "temp_mean_c", "soil_ph", "ndvi_mean", "humidity_pct"]:
                sv_val = getattr(source, f, 0) or 0
                dv_val = getattr(d, f, 0) or 0
                if sv_val: deltas[f] = round(((dv_val - sv_val) / sv_val) * 100, 1)
            use_case = f"{source.name} is similar to {d.name} for {crop or 'maize'} — {'strategies can transfer directly' if score > 0.9 else 'adapt recommendations for local differences'}."
            results.append({"district_id": d.id, "district_name": d.name, "province": d.province,
                            "similarity_score": round(score * 100, 1), "similarity_pct": f"{round(score*100,1)}%",
                            "elevation_m": d.elevation_mean, "rainfall_mm": d.rainfall_annual_mm,
                            "temp_c": d.temp_mean_c, "soil_type": d.soil_type, "soil_ph": d.soil_ph,
                            "ndvi": d.ndvi_mean, "humidity_pct": d.humidity_pct,
                            "flood_risk": d.flood_risk_score, "feature_deltas": deltas, "use_case": use_case})
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_n]

    async def build_matrix(self, districts: List):
        vecs = [self._vec(d) for d in districts]
        names = [d.name for d in districts]
        n = len(vecs)
        matrix = [[round(self._cosine(vecs[i], vecs[j]) * 100, 1) for j in range(n)] for i in range(n)]
        return {"districts": names, "matrix": matrix}
