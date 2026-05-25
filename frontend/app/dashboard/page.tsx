"use client";
import { useState, useEffect, useCallback } from "react";
import { getDistricts, predictSuitability, getSimilarDistricts, getClimateRisk, getForecast } from "@/lib/api";
import DataTools from "@/components/DataTools";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
         RadarChart, Radar, PolarGrid, PolarAngleAxis, Area, AreaChart, ReferenceLine } from "recharts";

const CROPS = ["potato","maize","bean","coffee","tea","banana"];
const VARIETIES: Record<string,string[]> = {
  potato:["Markies","Shangi","Victoria","Kinigi"],
  maize:["DK8031","RWILI","H614"],
  bean:["Lyamungu","Urwintore","RWR2245"],
  coffee:["Red Bourbon","Jackson"],
  tea:["Wufeng","Yabukita"],
  banana:["Gros Michel","Cavendish"],
};
const PROVINCES = ["All","Northern","Southern","Eastern","Western","Kigali City"];
const TABS = ["Prediction","Similarity","Climate","Forecast","Tools"] as const;
type Tab = typeof TABS[number];

function scoreColor(s:number){return s>=75?"#22c55e":s>=55?"#f59e0b":"#ef4444";}
function riskColor(s:number){return s>=65?"#ef4444":s>=40?"#f59e0b":"#22c55e";}
function badge(level:string){
  const c=level==="Low"?"bg-green-100 text-green-800":level==="Medium"?"bg-amber-100 text-amber-800":"bg-red-100 text-red-800";
  return <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${c}`}>{level}</span>;
}

function Card({label,value,sub,color}:{label:string;value:string;sub?:string;color?:string}){
  const b=color==="green"?"border-green-200 bg-green-50":color==="amber"?"border-amber-200 bg-amber-50":color==="red"?"border-red-200 bg-red-50":"border-gray-200 bg-white";
  return <div className={`rounded-xl border p-4 ${b}`}><div className="text-xs text-gray-500 mb-1">{label}</div><div className="text-2xl font-bold text-gray-900">{value}</div>{sub&&<div className="text-xs text-gray-400 mt-0.5">{sub}</div>}</div>;
}

function ShapBar({label,value,max}:{label:string;value:number;max:number}){
  const pct=Math.abs(value)/max*100;
  const isPos=value>=0;
  return (
    <div className="flex items-center gap-2 text-xs mb-2">
      <div className="w-44 text-gray-600 truncate text-right text-[11px]">{label}</div>
      <div className="flex-1 flex items-center gap-0.5">
        {!isPos&&<div className="flex-1 flex justify-end"><div className="h-4 rounded-sm bg-red-400" style={{width:`${pct}%`}}/></div>}
        <div className="w-px h-5 bg-gray-300"/>
        {isPos&&<div className="flex-1"><div className="h-4 rounded-sm bg-green-400" style={{width:`${pct}%`}}/></div>}
      </div>
      <div className={`w-12 text-right font-mono text-[11px] ${isPos?"text-green-700":"text-red-600"}`}>{isPos?"+":""}{value.toFixed(2)}</div>
    </div>
  );
}

export default function Dashboard(){
  const [districts,setDistricts]=useState<any[]>([]);
  const [filtered,setFiltered]=useState<any[]>([]);
  const [district,setDistrict]=useState<any>(null);
  const [crop,setCrop]=useState("maize");
  const [variety,setVariety]=useState("DK8031");
  const [province,setProvince]=useState("All");
  const [tab,setTab]=useState<Tab>("Prediction");
  const [prediction,setPrediction]=useState<any>(null);
  const [similar,setSimilar]=useState<any>(null);
  const [risk,setRisk]=useState<any>(null);
  const [forecast,setForecast]=useState<any>(null);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState<string|null>(null);

  useEffect(()=>{
    getDistricts().then((data:any[])=>{
      setDistricts(data); setFiltered(data);
      setDistrict(data.find((d:any)=>d.name==="Musanze")||data[0]);
    }).catch(()=>setError("Cannot connect to backend. Start the FastAPI server first (uvicorn app.main:app)."));
  },[]);

  useEffect(()=>{
    setFiltered(province==="All"?districts:districts.filter((d:any)=>d.province===province));
  },[province,districts]);

  const fetchData=useCallback(async()=>{
    if(!district)return;
    setLoading(true); setError(null);
    try{
      const[pred,sim,clim,fore]=await Promise.all([
        predictSuitability(district.id,crop,variety),
        getSimilarDistricts(district.id,5,"cosine",crop),
        getClimateRisk(district.id),
        getForecast(district.id,12),
      ]);
      setPrediction(pred); setSimilar(sim); setRisk(clim); setForecast(fore);
    }catch(e:any){setError(e.message);}
    finally{setLoading(false);}
  },[district,crop,variety]);

  useEffect(()=>{fetchData();},[fetchData]);

  const shapData=prediction?.shap_values
    ?Object.entries(prediction.shap_values as Record<string,number>).map(([k,v])=>({label:k,value:v})).sort((a,b)=>Math.abs(b.value)-Math.abs(a.value))
    :[];
  const maxShap=shapData.length?Math.max(...shapData.map((d:any)=>Math.abs(d.value))):1;

  const radarData=prediction?.feature_scores
    ?Object.entries(prediction.feature_scores as Record<string,number>).map(([k,v])=>({subject:k.replace("_"," "),score:v}))
    :[];

  const forecastChart=forecast?.forecasts?.slice(0,12).map((f:any)=>({
    month:f.month_label.split(" ")[0],rain:f.predicted_rainfall_mm,
    low:f.ci_low,high:f.ci_high,drought:Math.round(f.drought_probability*100),harvest:f.harvest_quality_score,
  }))||[];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* HEADER */}
      <header className="bg-green-800 text-white px-6 py-4 shadow-lg">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">🌱 RASIP</h1>
            <p className="text-green-200 text-xs">Rwanda Agricultural Spatial Intelligence Platform v2.0</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-green-200">
            <span className={`w-2 h-2 rounded-full ${loading?"bg-yellow-400 animate-pulse":"bg-green-400"}`}/>
            {loading?"Analysing...":"Live · Supabase PostgreSQL"}
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6 space-y-5">
        {error&&<div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">⚠️ {error}</div>}

        {/* CONTROLS */}
        <div className="bg-white border border-gray-200 rounded-xl p-4 flex flex-wrap gap-4 items-end shadow-sm">
          {[
            {label:"Province",value:province,onChange:(v:string)=>setProvince(v),options:PROVINCES},
            {label:"District",value:district?.id||"",onChange:(v:string)=>setDistrict(filtered.find((d:any)=>d.id===+v)),
             options:filtered.map((d:any)=>({value:d.id,label:`${d.name} (${d.province})`}))},
            {label:"Crop",value:crop,onChange:(v:string)=>{setCrop(v);setVariety(VARIETIES[v]?.[0]||"");},
             options:CROPS.map(c=>({value:c,label:c.charAt(0).toUpperCase()+c.slice(1)}))},
            {label:"Variety",value:variety,onChange:(v:string)=>setVariety(v),
             options:(VARIETIES[crop]||[]).map((v:string)=>({value:v,label:v}))},
          ].map(({label,value,onChange,options})=>(
            <div key={label}>
              <label className="block text-xs text-gray-500 mb-1 font-medium">{label}</label>
              <select className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white min-w-[130px]"
                      value={value} onChange={e=>onChange(e.target.value)}>
                {options.map((o:any)=>typeof o==="string"
                  ?<option key={o} value={o}>{o}</option>
                  :<option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
          ))}
          {district&&(
            <div className="ml-auto flex items-center gap-2 text-xs text-gray-500 flex-wrap">
              <span className="bg-amber-100 text-amber-800 px-2 py-0.5 rounded text-xs font-medium">{district.soil_type}</span>
              <span>pH {district.soil_ph}</span>
              <span>NDVI {district.ndvi_mean?.toFixed(2)}</span>
              <span>{district.elevation_mean?.toFixed(0)}m</span>
              <span className="hidden md:inline">{district.humidity_pct}% RH</span>
            </div>
          )}
        </div>

        {/* TABS */}
        <div className="flex gap-1 border-b border-gray-200">
          {TABS.map(t=>(
            <button key={t} onClick={()=>setTab(t)}
              className={`px-5 py-2.5 text-sm font-medium rounded-t-lg transition-colors ${
                tab===t?"bg-white border border-b-white border-gray-200 -mb-px text-green-800":"text-gray-500 hover:text-gray-700"
              }`}>
              {t==="Prediction"?"🌾 Prediction":t==="Similarity"?"🔄 Similarity":t==="Climate"?"🌤 Climate":t==="Forecast"?"📈 Forecast":"🛠 Tools"}
            </button>
          ))}
        </div>

        {/* ═══ PREDICTION TAB ═══ */}
        {tab==="Prediction"&&prediction&&(
          <div className="space-y-5">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card label="Suitability Score" value={`${prediction.suitability_score}%`} sub="8-feature AI model"
                    color={prediction.suitability_score>=75?"green":prediction.suitability_score>=55?"amber":"red"}/>
              <Card label="Yield Forecast" value={`${prediction.yield_prediction_t_ha} t/ha`} sub={variety}/>
              <Card label="Climate Risk" value={prediction.risk_level}
                    color={prediction.risk_level==="Low"?"green":prediction.risk_level==="Medium"?"amber":"red"}/>
              <Card label="Confidence" value={`${Math.round(prediction.confidence*100)}%`} sub="model v2.0"/>
            </div>

            <div className="bg-green-50 border border-green-200 rounded-xl p-4">
              <div className="text-xs font-semibold text-green-700 mb-1">🤖 AI Recommendation</div>
              <p className="text-sm text-green-900">{prediction.recommendation}</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
                <h3 className="text-sm font-semibold text-gray-800 mb-3">🧠 Explainable AI — SHAP Feature Impact</h3>
                <div className="text-[10px] text-gray-400 mb-3 flex justify-between"><span>← Limits growth</span><span>Boosts growth →</span></div>
                {shapData.map(({label,value}:any)=><ShapBar key={label} label={label} value={value} max={maxShap}/>)}
                <p className="text-[10px] text-gray-400 mt-3">Green = positive impact on suitability. Red = limiting factor.</p>
              </div>
              <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
                <h3 className="text-sm font-semibold text-gray-800 mb-2">🎯 Feature Score Radar</h3>
                <ResponsiveContainer width="100%" height={240}>
                  <RadarChart data={radarData}>
                    <PolarGrid/><PolarAngleAxis dataKey="subject" tick={{fontSize:10}}/>
                    <Radar name="Score" dataKey="score" stroke="#16a34a" fill="#16a34a" fillOpacity={0.25}/>
                    <Tooltip formatter={(v:any)=>[`${v}/100`,"Score"]}/>
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {(prediction.top_positive_factors?.length>0||prediction.top_negative_factors?.length>0)&&(
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-green-50 border border-green-200 rounded-xl p-4">
                  <div className="text-xs font-semibold text-green-700 mb-2">✅ Top Positive Factors</div>
                  <ul className="text-sm text-green-800 space-y-1">{prediction.top_positive_factors.map((f:string)=><li key={f}>+ {f}</li>)}</ul>
                </div>
                <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                  <div className="text-xs font-semibold text-red-700 mb-2">⚠️ Limiting Factors</div>
                  <ul className="text-sm text-red-800 space-y-1">{prediction.top_negative_factors.map((f:string)=><li key={f}>− {f}</li>)}</ul>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ═══ SIMILARITY TAB ═══ */}
        {tab==="Similarity"&&similar&&(
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-xl p-4">
              <div className="text-xs font-semibold text-green-700 mb-1">🔄 Cosine Similarity — Districts most like <strong>{similar.source_district}</strong></div>
              <p className="text-sm text-green-800">Computed using 11 features: rainfall, temperature, elevation, soil pH & type, humidity, NDVI, slope, flood risk, drought risk, and historical crop yields.</p>
            </div>
            {similar.similar_districts?.map((d:any,i:number)=>(
              <div key={d.district_id} className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-gray-400 text-sm">#{i+1}</span>
                    <span className="font-semibold text-gray-900">{d.district_name}</span>
                    <span className="text-gray-400 text-sm">{d.province}</span>
                    <span className="bg-amber-100 text-amber-800 px-2 py-0.5 rounded text-xs">{d.soil_type}</span>
                  </div>
                  <div className="text-right">
                    <div className="text-xl font-bold" style={{color:scoreColor(d.similarity_score)}}>{d.similarity_score}%</div>
                    <div className="text-xs text-gray-400">similarity</div>
                  </div>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2 mb-3">
                  <div className="h-2 rounded-full" style={{width:`${d.similarity_score}%`,backgroundColor:scoreColor(d.similarity_score)}}/>
                </div>
                <div className="grid grid-cols-4 gap-2 text-xs text-gray-500 mb-2">
                  <span>🌧 {d.rainfall_mm?.toFixed(0)}mm</span>
                  <span>🌡 {d.temp_c?.toFixed(1)}°C</span>
                  <span>📊 pH {d.soil_ph?.toFixed(1)}</span>
                  <span>🌿 {d.ndvi?.toFixed(2)} NDVI</span>
                </div>
                <div className="text-xs text-gray-600 italic border-t border-gray-100 pt-2">💡 {d.use_case}</div>
              </div>
            ))}
          </div>
        )}

        {/* ═══ CLIMATE TAB ═══ */}
        {tab==="Climate"&&risk&&(
          <div className="space-y-5">
            <div className="grid grid-cols-3 gap-4">
              {[{label:"Flood Risk",score:risk.flood_risk_score,icon:"🌊"},{label:"Drought Risk",score:risk.drought_risk_score,icon:"☀️"},{label:"Soil Degradation",score:risk.soil_degradation_score,icon:"🏜️"}].map(({label,score,icon})=>(
                <div key={label} className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm text-center">
                  <div className="text-2xl mb-1">{icon}</div>
                  <div className="text-xs text-gray-500 mb-2">{label}</div>
                  <div className="text-3xl font-bold mb-2" style={{color:riskColor(score)}}>{score?.toFixed(0)}</div>
                  <div className="w-full bg-gray-100 rounded-full h-2"><div className="h-2 rounded-full" style={{width:`${score}%`,backgroundColor:riskColor(score)}}/></div>
                  <div className="text-xs text-gray-400 mt-1">/ 100</div>
                </div>
              ))}
            </div>
            <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
              <h3 className="text-sm font-semibold mb-3">🌿 Vegetation Health (NDVI) — {risk.ndvi_status}</h3>
              <div className="flex items-center gap-4">
                <div className="text-4xl font-bold text-green-700">{district?.ndvi_mean?.toFixed(3)}</div>
                <div>
                  <div className="text-sm text-gray-600">Trend: {(district?.ndvi_trend||0)>=0?"▲":"▼"} {Math.abs(district?.ndvi_trend||0).toFixed(3)}/yr</div>
                  <div className="text-xs text-gray-400">Overall risk: {risk.overall_risk}</div>
                </div>
                <div className="flex-1">
                  <div className="text-xs text-gray-400 mb-1">−1 (bare) → +1 (dense vegetation)</div>
                  <div className="relative w-full bg-gradient-to-r from-red-200 via-yellow-200 to-green-400 rounded-full h-3">
                    <div className="absolute top-0 w-3 h-3 bg-white border-2 border-gray-600 rounded-full transform -translate-x-1/2"
                         style={{left:`${((district?.ndvi_mean||0)+1)/2*100}%`}}/>
                  </div>
                </div>
              </div>
            </div>
            <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
              <h3 className="text-sm font-semibold mb-3">📋 Risk Recommendations</h3>
              {risk.recommendations?.map((r:string,i:number)=><div key={i} className="text-sm text-gray-700 py-2 border-b border-gray-100 last:border-0">{r}</div>)}
            </div>
            {district&&(
              <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
                <h3 className="text-sm font-semibold mb-3">☕ Rwanda Special Crops Suitability</h3>
                <div className="grid grid-cols-3 gap-3">
                  {[{label:"Coffee",key:"coffee_suitable",yKey:"avg_coffee_yield",icon:"☕"},{label:"Tea",key:"tea_suitable",yKey:"avg_tea_yield",icon:"🍵"},{label:"Banana",key:"banana_suitable",yKey:null,icon:"🍌"}].map(({label,key,yKey,icon})=>(
                    <div key={label} className={`rounded-lg p-3 text-center border ${district[key]?"border-green-200 bg-green-50":"border-gray-200 bg-gray-50 opacity-60"}`}>
                      <div className="text-xl mb-1">{icon}</div>
                      <div className="text-xs font-medium">{label}</div>
                      {district[key]?<div className="text-xs text-green-700 font-semibold mt-0.5">✓ Suitable{yKey&&district[yKey]>0?<span className="block">{district[yKey].toFixed(1)} t/ha</span>:null}</div>:<div className="text-xs text-gray-400 mt-0.5">Not suitable</div>}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ═══ FORECAST TAB ═══ */}
        {tab==="Forecast"&&forecast&&(
          <div className="space-y-5">
            {forecast.drought_warning&&(
              <div className={`rounded-xl border p-4 ${forecast.drought_warning.warning_level==="Critical"?"bg-red-50 border-red-200":forecast.drought_warning.warning_level==="High"?"bg-orange-50 border-orange-200":forecast.drought_warning.warning_level==="Moderate"?"bg-amber-50 border-amber-200":"bg-green-50 border-green-200"}`}>
                <div className="flex items-center justify-between mb-1">
                  <div className="text-xs font-semibold text-gray-700">🌡 Drought Early Warning</div>
                  {badge(forecast.drought_warning.warning_level)}
                </div>
                <p className="text-sm text-gray-700">{forecast.drought_warning.recommendation}</p>
                <div className="text-xs text-gray-400 mt-1">Monitoring: {forecast.drought_warning.monitoring_frequency}</div>
              </div>
            )}
            <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
              <h3 className="text-sm font-semibold mb-4">🌧 12-Month Rainfall Forecast (mm) with Confidence Interval</h3>
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={forecastChart}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
                  <XAxis dataKey="month" tick={{fontSize:11}}/><YAxis tick={{fontSize:11}}/>
                  <Tooltip formatter={(v:any,n:string)=>[`${v}mm`,n==="rain"?"Predicted":n==="high"?"CI High":"CI Low"]}/>
                  <Area type="monotone" dataKey="high" stroke="none" fill="#bbf7d0" fillOpacity={0.5}/>
                  <Area type="monotone" dataKey="low" stroke="none" fill="#fff" fillOpacity={1}/>
                  <Line type="monotone" dataKey="rain" stroke="#16a34a" strokeWidth={2} dot={false}/>
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
                <h3 className="text-sm font-semibold mb-4">☀️ Drought Probability (%)</h3>
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={forecastChart}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
                    <XAxis dataKey="month" tick={{fontSize:9}}/><YAxis domain={[0,100]} tick={{fontSize:10}}/>
                    <Tooltip formatter={(v:any)=>[`${v}%`,"Drought risk"]}/>
                    <ReferenceLine y={50} stroke="#f59e0b" strokeDasharray="3 3"/>
                    <Bar dataKey="drought" fill="#f97316" radius={[3,3,0,0]}/>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
                <h3 className="text-sm font-semibold mb-4">🌾 Harvest Quality Score (0–100)</h3>
                <ResponsiveContainer width="100%" height={180}>
                  <LineChart data={forecastChart}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
                    <XAxis dataKey="month" tick={{fontSize:9}}/><YAxis domain={[0,100]} tick={{fontSize:10}}/>
                    <Tooltip formatter={(v:any)=>[v,"Quality"]}/>
                    <ReferenceLine y={70} stroke="#16a34a" strokeDasharray="3 3"/>
                    <Line type="monotone" dataKey="harvest" stroke="#16a34a" strokeWidth={2} dot={false}/>
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
              <h3 className="text-sm font-semibold mb-3">📅 Monthly Alerts</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {forecast.forecasts?.filter((f:any)=>f.alert).slice(0,6).map((f:any)=>(
                  <div key={f.month_label} className="text-xs bg-gray-50 rounded-lg p-2 border border-gray-100">
                    <div className="font-medium text-gray-700 mb-0.5">{f.month_label}</div>
                    <div>{f.alert}</div>
                    <div className="text-gray-400 mt-0.5 text-[10px]">{f.season}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        
        {/* ═══ TOOLS TAB ═══ */}
        {tab==="Tools"&&(
          <DataTools
            districts={districts}
            currentDistrict={district}
            currentCrop={crop}
            currentVariety={variety}
            prediction={prediction}
            risk={risk}
            forecast={forecast}
            similar={similar}
          />
        )}

        {loading&&<div className="fixed inset-0 bg-black/20 flex items-center justify-center z-50"><div className="bg-white rounded-xl p-6 shadow-xl text-sm text-gray-700">🔄 Running AI analysis...</div></div>}
      </div>

      <footer className="bg-white border-t border-gray-200 mt-12 py-4 text-center text-xs text-gray-400">
        RASIP v2.0 · Rwanda Agricultural Spatial Intelligence Platform · Free Stack: Supabase + Render + Vercel
      </footer>
    </div>
  );
}
