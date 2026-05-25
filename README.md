# 🌱 RASIP — Rwanda Agricultural Spatial Intelligence Platform v2.0

> AI + GIS system for Rwanda agriculture. **100% free-tier stack.**

---

## 🗄 Database: NeonDB (Free PostgreSQL)

**Connection string (already configured in `.env`):**
```
postgresql://neondb_owner:npg_oDfcQNEVy7h4@ep-withered-sky-alk11h6b-pooler.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require
```

### Step 1 — Run SQL in NeonDB Console
1. Go to [console.neon.tech](https://console.neon.tech)
2. Open **SQL Editor**
3. Paste and run the entire `neondb_setup.sql` file
4. You should see: **districts=30, crop_trials=~165, climate_records=720**

---

## 🚀 Local Setup (Windows)

### Backend
```cmd
cd C:\Users\Francis Musoke\OneDrive\Documents\Github\rasip\backend

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

:: .env is already configured with NeonDB
uvicorn app.main:app --reload --port 8000
```
API docs → http://localhost:8000/docs

### Frontend
```cmd
cd C:\Users\Francis Musoke\OneDrive\Documents\Github\rasip\frontend

npm install
npm run dev
```
Dashboard → http://localhost:3000

---

## 🌐 Deploy (Free)

### Backend → Render.com
1. Push to GitHub
2. New Web Service: connect your repo
3. Build: `cd backend && pip install -r requirements.txt`
4. Start: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add env vars (copy from `.env`)

### Frontend → Vercel
```cmd
cd frontend
npx vercel --prod
```
Set `NEXT_PUBLIC_API_URL` = your Render URL

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🌾 Crop Suitability AI | 8-feature model: soil pH, type, humidity, NDVI, yield, flood risk, temperature, elevation |
| 🔄 District Similarity | Cosine similarity — *"Bugesera is similar to Nyagatare for maize"* |
| 📈 Climate Forecast | 12-month rainfall, drought probability, harvest quality |
| 🧠 Explainable AI | SHAP attribution — *why* each prediction was made |
| ☀️ Drought Warning | Real-time early warning + recommendations |
| ☕ Rwanda Crops | Coffee, tea, banana suitability per district |

---

## 📡 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/districts/` | All 30 districts |
| `POST /api/v1/predict/suitability` | Crop suitability AI |
| `GET /api/v1/similarity/{id}` | Similar districts |
| `GET /api/v1/climate/risk/{id}` | Climate risks |
| `GET /api/v1/forecast/{id}` | 12-month forecast |
| `GET /docs` | Swagger UI |

---

## 🛠 Tech Stack

| Layer | Tech | Cost |
|-------|------|------|
| Frontend | Next.js + Tailwind + Recharts | Free (Vercel) |
| Backend | FastAPI + Python | Free (Render) |
| Database | NeonDB PostgreSQL | Free (0.5GB) |
| ML | scikit-learn, XGBoost, SHAP | Free/OSS |
| CI/CD | GitHub Actions | Free |
