"""Climate forecasting service — 12-month statistical forecast."""
import math, random
from typing import List, Dict, Any

RAIN_SEASONALITY = {1:0.75,2:0.90,3:1.45,4:1.60,5:1.30,6:0.50,7:0.40,8:0.55,9:1.20,10:1.35,11:1.30,12:0.70}
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def _season(m):
    if m in (3,4,5): return "Itumba (Long Rain)"
    if m in (9,10,11): return "Umuhindo (Short Rain)"
    if m in (6,7,8): return "Impeshi (Long Dry)"
    return "Urugaryi (Short Dry)"

class ForecastService:
    def forecast_district(self, district, months_ahead=12):
        import datetime
        now = datetime.date.today()
        rng = random.Random(district.id * 1000)
        base_rain = district.rainfall_annual_mm / 12
        forecasts = []
        for i in range(months_ahead):
            fm = (now.month + i - 1) % 12 + 1
            fy = now.year + (now.month + i - 1) // 12
            rf = RAIN_SEASONALITY.get(fm, 1.0)
            rain = base_rain * rf * rng.uniform(0.80, 1.20)
            temp = district.temp_mean_c + 0.5 * math.cos((fm - 4) * math.pi / 6) + rng.uniform(-0.5, 0.5)
            drought_prob = max(0.0, min(1.0, (district.drought_risk_score / 100) * (1 - rf * 0.5) + rng.uniform(-0.05, 0.05)))
            flood_prob = max(0.0, min(1.0, (district.flood_risk_score / 100) * rf * 0.8 + rng.uniform(-0.05, 0.05)))
            crop_fail = max(0.0, min(1.0, drought_prob * 0.6 + flood_prob * 0.3))
            harvest_q = max(0.0, min(100.0, 100 - drought_prob * 40 - flood_prob * 25 - max(0, temp - 25) * 3))
            ci_w = rain * (0.15 + i * 0.02)
            alert = ("⚠️ High drought risk" if drought_prob > 0.7 else
                     "⚠️ High flood risk" if flood_prob > 0.7 else
                     "⚡ Moderate drought risk" if drought_prob > 0.5 else
                     "✅ Good planting conditions" if fm in (3,4,9,10) else "")
            forecasts.append({"month": fm, "year": fy, "month_label": f"{MONTHS[fm-1]} {fy}",
                              "predicted_rainfall_mm": round(rain, 1), "ci_low": round(max(0, rain - ci_w), 1),
                              "ci_high": round(rain + ci_w, 1), "predicted_temp_c": round(temp, 1),
                              "drought_probability": round(drought_prob, 3), "flood_probability": round(flood_prob, 3),
                              "crop_failure_probability": round(crop_fail, 3), "harvest_quality_score": round(harvest_q, 1),
                              "season": _season(fm), "alert": alert})
        return forecasts

    def get_drought_early_warning(self, district):
        risk = district.drought_risk_score or 30
        level = "Critical" if risk >= 65 else "High" if risk >= 45 else "Moderate" if risk >= 25 else "Low"
        recs = {"Critical": f"URGENT: {district.name} faces severe drought. Activate emergency irrigation; use drought-tolerant varieties.",
                "High": f"{district.name} has high drought risk. Implement water conservation and mulching.",
                "Moderate": f"{district.name} has moderate drought risk. Monitor rainfall weekly.",
                "Low": f"{district.name} has low drought risk. Continue standard practices."}
        return {"district": district.name, "drought_risk_score": risk, "warning_level": level,
                "ndvi_trend": district.ndvi_trend, "recommendation": recs[level],
                "monitoring_frequency": "Weekly" if level in ("Critical","High") else "Monthly"}
