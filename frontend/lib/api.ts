const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function api(path: string, options?: RequestInit) {
  const res = await fetch(`${BASE}${path}`, { headers: { "Content-Type": "application/json" }, ...options });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export const getDistricts = (province?: string) => api(`/api/v1/districts/${province ? `?province=${province}` : ""}`);
export const getDistrict = (id: number) => api(`/api/v1/districts/${id}`);
export const predictSuitability = (district_id: number, crop: string, variety?: string) =>
  api("/api/v1/predict/suitability", { method: "POST", body: JSON.stringify({ district_id, crop, variety }) });
export const predictYield = (district_id: number, crop: string, rainfall_mm?: number) =>
  api("/api/v1/predict/yield", { method: "POST", body: JSON.stringify({ district_id, crop, rainfall_mm }) });
export const getPredictionHistory = (district_id: number) => api(`/api/v1/predict/history/${district_id}`);
export const getCrops = () => api("/api/v1/predict/crops");
export const getVarieties = (crop: string) => api(`/api/v1/predict/varieties/${crop}`);
export const getSimilarDistricts = (district_id: number, top_n = 5, method = "cosine", crop?: string) =>
  api(`/api/v1/similarity/${district_id}?top_n=${top_n}&method=${method}${crop ? `&crop=${crop}` : ""}`);
export const getSimilarityMatrix = () => api("/api/v1/similarity/matrix/all");
export const getClimateRisk = (district_id: number) => api(`/api/v1/climate/risk/${district_id}`);
export const getClimateHistory = (district_id: number, year?: number) =>
  api(`/api/v1/climate/history/${district_id}${year ? `?year=${year}` : ""}`);
export const getAllRisks = () => api("/api/v1/climate/all-risks");
export const getForecast = (district_id: number, months = 12) => api(`/api/v1/forecast/${district_id}?months=${months}`);
export const getDroughtWarning = (district_id: number) => api(`/api/v1/forecast/warning/${district_id}`);
