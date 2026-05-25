"use client";
import { useState, useRef, useCallback } from "react";

// ─── Types ──────────────────────────────────────────────────────────────────
interface CSVRow {
  district: string;
  crop: string;
  variety?: string;
  [key: string]: string | undefined;
}

interface ParsedCSV {
  headers: string[];
  rows: CSVRow[];
  errors: string[];
}

interface ReportData {
  district: any;
  crop: string;
  variety: string;
  prediction: any;
  risk: any;
  forecast: any;
  similar: any;
}

// ─── CSV Parser ──────────────────────────────────────────────────────────────
function parseCSV(text: string): ParsedCSV {
  const lines = text.trim().split(/\r?\n/);
  const errors: string[] = [];
  if (lines.length < 2) return { headers: [], rows: [], errors: ["CSV must have a header row and at least one data row."] };

  const headers = lines[0].split(",").map(h => h.trim().toLowerCase().replace(/\s+/g, "_"));
  if (!headers.includes("district")) errors.push("Missing required column: district");
  if (!headers.includes("crop")) errors.push("Missing required column: crop");

  const rows: CSVRow[] = lines.slice(1).filter(l => l.trim()).map((line, i) => {
    const vals = line.split(",").map(v => v.trim());
    const row: CSVRow = { district: "", crop: "" };
    headers.forEach((h, j) => { row[h] = vals[j] ?? ""; });
    if (!row.district) errors.push(`Row ${i + 2}: missing district`);
    if (!row.crop) errors.push(`Row ${i + 2}: missing crop`);
    return row;
  });

  return { headers, rows, errors };
}

// ─── Report Generator ────────────────────────────────────────────────────────
function generateHTMLReport(data: ReportData): string {
  const { district, crop, variety, prediction, risk, forecast } = data;
  const date = new Date().toLocaleDateString("en-GB", { day: "2-digit", month: "long", year: "numeric" });
  const score = prediction?.suitability_score ?? "N/A";
  const yieldVal = prediction?.yield_prediction_t_ha ?? "N/A";
  const riskLevel = prediction?.risk_level ?? "N/A";
  const conf = prediction ? `${Math.round(prediction.confidence * 100)}%` : "N/A";

  const shapRows = prediction?.shap_values
    ? Object.entries(prediction.shap_values as Record<string, number>)
        .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
        .map(([k, v]) => `<tr><td>${k}</td><td style="color:${v >= 0 ? "#16a34a" : "#dc2626"};font-weight:600">${v >= 0 ? "+" : ""}${v.toFixed(3)}</td></tr>`)
        .join("")
    : "";

  const forecastRows = forecast?.forecasts?.slice(0, 6).map((f: any) =>
    `<tr><td>${f.month_label}</td><td>${f.predicted_rainfall_mm?.toFixed(0)} mm</td><td>${Math.round(f.drought_probability * 100)}%</td><td>${f.harvest_quality_score?.toFixed(0)}</td></tr>`
  ).join("") ?? "";

  const posFactors = prediction?.top_positive_factors?.map((f: string) => `<li>✅ ${f}</li>`).join("") ?? "";
  const negFactors = prediction?.top_negative_factors?.map((f: string) => `<li>⚠️ ${f}</li>`).join("") ?? "";
  const recommendations = risk?.recommendations?.map((r: string) => `<li>${r}</li>`).join("") ?? "";

  const scoreColor = score >= 75 ? "#16a34a" : score >= 55 ? "#d97706" : "#dc2626";
  const riskBg = riskLevel === "Low" ? "#dcfce7" : riskLevel === "Medium" ? "#fef3c7" : "#fee2e2";
  const riskFg = riskLevel === "Low" ? "#15803d" : riskLevel === "Medium" ? "#92400e" : "#991b1b";

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<title>RASIP Report — ${district?.name ?? "Unknown"} · ${crop}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;600&display=swap');
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'DM Sans',sans-serif;background:#f9fafb;color:#111827;padding:40px;max-width:900px;margin:0 auto}
  .header{background:linear-gradient(135deg,#14532d 0%,#166534 60%,#15803d 100%);color:white;padding:36px 40px;border-radius:16px;margin-bottom:32px}
  .header h1{font-family:'DM Serif Display',serif;font-size:28px;margin-bottom:4px}
  .header .sub{opacity:0.75;font-size:13px;margin-bottom:16px}
  .meta{display:flex;gap:24px;font-size:13px;opacity:0.85}
  .section{background:white;border:1px solid #e5e7eb;border-radius:12px;padding:24px;margin-bottom:20px}
  .section h2{font-size:14px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#6b7280;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid #f3f4f6}
  .kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:0}
  .kpi{background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;padding:16px;text-align:center}
  .kpi .label{font-size:11px;color:#9ca3af;margin-bottom:6px}
  .kpi .value{font-size:24px;font-weight:700}
  .kpi .sub{font-size:11px;color:#9ca3af;margin-top:4px}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th{text-align:left;padding:8px 12px;background:#f9fafb;font-size:11px;text-transform:uppercase;letter-spacing:0.05em;color:#6b7280;border-bottom:2px solid #e5e7eb}
  td{padding:8px 12px;border-bottom:1px solid #f3f4f6}
  tr:last-child td{border-bottom:none}
  .two-col{display:grid;grid-template-columns:1fr 1fr;gap:20px}
  ul{padding-left:0;list-style:none}
  ul li{font-size:13px;padding:6px 0;border-bottom:1px solid #f3f4f6;color:#374151}
  ul li:last-child{border-bottom:none}
  .risk-badge{display:inline-block;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;background:${riskBg};color:${riskFg}}
  .score-ring{font-size:48px;font-weight:700;color:${scoreColor}}
  .footer{text-align:center;font-size:11px;color:#9ca3af;margin-top:32px;padding-top:16px;border-top:1px solid #e5e7eb}
  @media print{body{padding:20px}.section{page-break-inside:avoid}}
</style>
</head>
<body>
<div class="header">
  <h1>🌱 RASIP Agricultural Report</h1>
  <p class="sub">Rwanda Agricultural Spatial Intelligence Platform v2.0</p>
  <div class="meta">
    <span>📍 ${district?.name ?? "Unknown District"}, ${district?.province ?? ""}</span>
    <span>🌾 ${crop.charAt(0).toUpperCase() + crop.slice(1)} — ${variety}</span>
    <span>📅 ${date}</span>
    <span>🏔 ${district?.elevation_mean?.toFixed(0) ?? "—"}m elevation</span>
  </div>
</div>

<div class="section">
  <h2>Suitability Summary</h2>
  <div class="kpi-grid">
    <div class="kpi"><div class="label">Suitability Score</div><div class="value score-ring">${score}%</div><div class="sub">AI Model v2.0</div></div>
    <div class="kpi"><div class="label">Yield Forecast</div><div class="value">${yieldVal}</div><div class="sub">t/ha</div></div>
    <div class="kpi"><div class="label">Climate Risk</div><div class="value" style="font-size:18px;padding-top:6px"><span class="risk-badge">${riskLevel}</span></div></div>
    <div class="kpi"><div class="label">Confidence</div><div class="value">${conf}</div><div class="sub">Model certainty</div></div>
  </div>
</div>

${prediction?.recommendation ? `
<div class="section">
  <h2>AI Recommendation</h2>
  <p style="font-size:14px;line-height:1.7;color:#374151">${prediction.recommendation}</p>
</div>` : ""}

<div class="two-col">
  ${posFactors || negFactors ? `
  <div class="section">
    <h2>Key Factors</h2>
    ${posFactors ? `<p style="font-size:11px;color:#16a34a;font-weight:600;margin-bottom:6px">POSITIVE</p><ul>${posFactors}</ul>` : ""}
    ${negFactors ? `<p style="font-size:11px;color:#dc2626;font-weight:600;margin:12px 0 6px">LIMITING</p><ul>${negFactors}</ul>` : ""}
  </div>` : ""}

  ${shapRows ? `
  <div class="section">
    <h2>Feature Impact (SHAP)</h2>
    <table><thead><tr><th>Feature</th><th>Impact</th></tr></thead><tbody>${shapRows}</tbody></table>
  </div>` : ""}
</div>

${risk ? `
<div class="section">
  <h2>Climate Risk Assessment</h2>
  <div class="kpi-grid" style="grid-template-columns:repeat(3,1fr)">
    <div class="kpi"><div class="label">🌊 Flood Risk</div><div class="value" style="color:#2563eb">${risk.flood_risk_score?.toFixed(0) ?? "—"}</div><div class="sub">/ 100</div></div>
    <div class="kpi"><div class="label">☀️ Drought Risk</div><div class="value" style="color:#d97706">${risk.drought_risk_score?.toFixed(0) ?? "—"}</div><div class="sub">/ 100</div></div>
    <div class="kpi"><div class="label">🏜️ Soil Degradation</div><div class="value" style="color:#92400e">${risk.soil_degradation_score?.toFixed(0) ?? "—"}</div><div class="sub">/ 100</div></div>
  </div>
  ${recommendations ? `<div style="margin-top:16px"><p style="font-size:11px;color:#6b7280;font-weight:600;margin-bottom:8px">RECOMMENDATIONS</p><ul>${recommendations}</ul></div>` : ""}
</div>` : ""}

${forecastRows ? `
<div class="section">
  <h2>6-Month Forecast</h2>
  <table>
    <thead><tr><th>Month</th><th>Rainfall</th><th>Drought Risk</th><th>Harvest Score</th></tr></thead>
    <tbody>${forecastRows}</tbody>
  </table>
</div>` : ""}

<div class="footer">
  RASIP v2.0 · Generated ${date} · Rwanda Agricultural Spatial Intelligence Platform · Free Stack: Supabase + Render + Vercel
</div>
</body>
</html>`;
}

// ─── CSV Template ─────────────────────────────────────────────────────────────
const CSV_TEMPLATE = `district,crop,variety
Musanze,potato,Kinigi
Rubavu,maize,DK8031
Nyamagabe,coffee,Red Bourbon
Huye,bean,Urwintore
Rwamagana,banana,Cavendish
`;

// ─── Main Component ───────────────────────────────────────────────────────────
interface DataToolsProps {
  districts: any[];
  currentDistrict: any;
  currentCrop: string;
  currentVariety: string;
  prediction: any;
  risk: any;
  forecast: any;
  similar: any;
}

export default function DataTools({
  districts,
  currentDistrict,
  currentCrop,
  currentVariety,
  prediction,
  risk,
  forecast,
  similar,
}: DataToolsProps) {
  const [csvData, setCsvData] = useState<ParsedCSV | null>(null);
  const [csvText, setCsvText] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [uploadMode, setUploadMode] = useState<"drop" | "paste">("drop");
  const [batchResults, setBatchResults] = useState<any[]>([]);
  const [batchRunning, setBatchRunning] = useState(false);
  const [batchProgress, setBatchProgress] = useState(0);
  const [reportFormat, setReportFormat] = useState<"html" | "json" | "csv">("html");
  const fileRef = useRef<HTMLInputElement>(null);

  // ── File handling ──
  const processFile = useCallback((file: File) => {
    if (!file.name.endsWith(".csv") && file.type !== "text/csv") {
      alert("Please upload a .csv file");
      return;
    }
    const reader = new FileReader();
    reader.onload = e => {
      const text = e.target?.result as string;
      setCsvText(text);
      setCsvData(parseCSV(text));
      setBatchResults([]);
    };
    reader.readAsText(file);
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  }, [processFile]);

  const onPasteChange = (text: string) => {
    setCsvText(text);
    if (text.trim()) setCsvData(parseCSV(text));
    else setCsvData(null);
    setBatchResults([]);
  };

  const downloadTemplate = () => {
    const blob = new Blob([CSV_TEMPLATE], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "rasip_template.csv";
    a.click();
  };

  // ── Batch run ──
  const runBatch = async () => {
    if (!csvData || csvData.errors.length > 0) return;
    setBatchRunning(true);
    setBatchProgress(0);
    const results: any[] = [];
    const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    for (let i = 0; i < csvData.rows.length; i++) {
      const row = csvData.rows[i];
      setBatchProgress(Math.round((i / csvData.rows.length) * 100));
      const dist = districts.find(d => d.name.toLowerCase() === row.district.toLowerCase());
      if (!dist) {
        results.push({ ...row, error: `District "${row.district}" not found`, status: "error" });
        continue;
      }
      try {
        const res = await fetch(`${BASE}/api/v1/predict/suitability`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ district_id: dist.id, crop: row.crop, variety: row.variety || undefined }),
        });
        const data = await res.json();
        results.push({ ...row, district_id: dist.id, province: dist.province, ...data, status: "ok" });
      } catch {
        results.push({ ...row, error: "API error", status: "error" });
      }
    }
    setBatchResults(results);
    setBatchProgress(100);
    setBatchRunning(false);
  };

  // ── Report download ──
  const downloadReport = () => {
    const data: ReportData = {
      district: currentDistrict,
      crop: currentCrop,
      variety: currentVariety,
      prediction,
      risk,
      forecast,
      similar,
    };

    if (reportFormat === "html") {
      const html = generateHTMLReport(data);
      const blob = new Blob([html], { type: "text/html" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `RASIP_${currentDistrict?.name ?? "report"}_${currentCrop}_${new Date().toISOString().slice(0, 10)}.html`;
      a.click();
    } else if (reportFormat === "json") {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `RASIP_${currentDistrict?.name ?? "report"}_${currentCrop}_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
    } else {
      // CSV summary
      const headers = "district,province,crop,variety,suitability_score,yield_t_ha,risk_level,confidence,recommendation";
      const row = [
        currentDistrict?.name ?? "",
        currentDistrict?.province ?? "",
        currentCrop,
        currentVariety,
        prediction?.suitability_score ?? "",
        prediction?.yield_prediction_t_ha ?? "",
        prediction?.risk_level ?? "",
        prediction ? Math.round(prediction.confidence * 100) + "%" : "",
        `"${(prediction?.recommendation ?? "").replace(/"/g, "'")}"`,
      ].join(",");
      const blob = new Blob([headers + "\n" + row], { type: "text/csv" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `RASIP_${currentDistrict?.name ?? "report"}_${currentCrop}_${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
    }
  };

  const downloadBatchCSV = () => {
    if (!batchResults.length) return;
    const headers = "district,province,crop,variety,suitability_score,yield_t_ha,risk_level,confidence,status,error";
    const rows = batchResults.map(r =>
      [r.district, r.province ?? "", r.crop, r.variety ?? "", r.suitability_score ?? "", r.yield_prediction_t_ha ?? "", r.risk_level ?? "", r.confidence ? Math.round(r.confidence * 100) + "%" : "", r.status, r.error ?? ""].join(",")
    );
    const blob = new Blob([[headers, ...rows].join("\n")], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `RASIP_batch_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
  };

  return (
    <div className="space-y-6">

      {/* ── REPORT DOWNLOAD ─────────────────────────────────────────────── */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-gray-800 mb-1">📥 Download Current Report</h3>
        <p className="text-xs text-gray-400 mb-4">
          Export the active analysis for <strong>{currentDistrict?.name ?? "—"}</strong> · {currentCrop} ({currentVariety})
        </p>

        {!prediction && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-700 mb-4">
            ⚠️ Run a prediction first (select district + crop) before downloading a report.
          </div>
        )}

        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-xs text-gray-500 mb-1 font-medium">Format</label>
            <div className="flex rounded-lg border border-gray-200 overflow-hidden">
              {(["html", "json", "csv"] as const).map(f => (
                <button
                  key={f}
                  onClick={() => setReportFormat(f)}
                  className={`px-4 py-2 text-xs font-medium transition-colors ${reportFormat === f ? "bg-green-800 text-white" : "bg-white text-gray-600 hover:bg-gray-50"}`}
                >
                  {f === "html" ? "🌐 HTML" : f === "json" ? "{ } JSON" : "📊 CSV"}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={downloadReport}
            disabled={!prediction}
            className="flex items-center gap-2 bg-green-800 hover:bg-green-700 disabled:bg-gray-200 disabled:text-gray-400 text-white px-5 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            ⬇️ Download Report
          </button>

          <div className="text-xs text-gray-400 ml-auto self-center">
            {reportFormat === "html" && "Full styled report — open in browser or print to PDF"}
            {reportFormat === "json" && "Machine-readable data — for developers / GIS tools"}
            {reportFormat === "csv" && "Spreadsheet row — append to your tracking sheet"}
          </div>
        </div>
      </div>

      {/* ── CSV UPLOAD ───────────────────────────────────────────────────── */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-800">📤 Batch CSV Upload</h3>
            <p className="text-xs text-gray-400 mt-0.5">Run predictions for multiple districts at once</p>
          </div>
          <button onClick={downloadTemplate} className="text-xs text-green-700 hover:text-green-900 border border-green-200 rounded-lg px-3 py-1.5 hover:bg-green-50 transition-colors">
            ⬇️ Download template
          </button>
        </div>

        {/* Mode toggle */}
        <div className="flex gap-1 mb-4 bg-gray-100 rounded-lg p-0.5 w-fit">
          {(["drop", "paste"] as const).map(m => (
            <button key={m} onClick={() => setUploadMode(m)}
              className={`px-4 py-1.5 text-xs font-medium rounded-md transition-colors ${uploadMode === m ? "bg-white text-gray-900 shadow-sm" : "text-gray-500"}`}>
              {m === "drop" ? "📂 Upload file" : "📋 Paste CSV"}
            </button>
          ))}
        </div>

        {uploadMode === "drop" ? (
          <div
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            onClick={() => fileRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${dragOver ? "border-green-500 bg-green-50" : "border-gray-200 hover:border-green-300 hover:bg-gray-50"}`}
          >
            <div className="text-3xl mb-2">{dragOver ? "✅" : "📂"}</div>
            <div className="text-sm text-gray-600 font-medium">{dragOver ? "Drop to upload" : "Drag & drop a CSV file here"}</div>
            <div className="text-xs text-gray-400 mt-1">or click to browse · .csv only</div>
            <input ref={fileRef} type="file" accept=".csv,text/csv" className="hidden"
              onChange={e => { if (e.target.files?.[0]) processFile(e.target.files[0]); }} />
          </div>
        ) : (
          <textarea
            value={csvText}
            onChange={e => onPasteChange(e.target.value)}
            placeholder={"district,crop,variety\nMusanze,potato,Kinigi\nRubavu,maize,DK8031"}
            rows={6}
            className="w-full border border-gray-200 rounded-xl p-3 text-xs font-mono text-gray-700 resize-y focus:outline-none focus:ring-2 focus:ring-green-300"
          />
        )}

        {/* Errors */}
        {csvData?.errors && csvData.errors.length > 0 && (
          <div className="mt-3 bg-red-50 border border-red-200 rounded-lg p-3">
            <div className="text-xs font-semibold text-red-700 mb-1">⚠️ Validation errors</div>
            {csvData.errors.map((e, i) => <div key={i} className="text-xs text-red-600">{e}</div>)}
          </div>
        )}

        {/* Preview */}
        {csvData && csvData.errors.length === 0 && (
          <div className="mt-4">
            <div className="flex items-center justify-between mb-2">
              <div className="text-xs text-gray-500 font-medium">{csvData.rows.length} rows ready · Columns: {csvData.headers.join(", ")}</div>
              <button
                onClick={runBatch}
                disabled={batchRunning}
                className="bg-green-800 hover:bg-green-700 disabled:bg-gray-200 text-white disabled:text-gray-400 text-xs px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
              >
                {batchRunning ? `⏳ Running… ${batchProgress}%` : "▶ Run Batch"}
              </button>
            </div>
            {/* Progress bar */}
            {batchRunning && (
              <div className="w-full bg-gray-100 rounded-full h-1.5 mb-3">
                <div className="bg-green-600 h-1.5 rounded-full transition-all duration-300" style={{ width: `${batchProgress}%` }} />
              </div>
            )}

            <div className="overflow-x-auto rounded-lg border border-gray-100">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-gray-50">
                    {csvData.headers.map(h => <th key={h} className="text-left px-3 py-2 text-gray-500 font-medium">{h}</th>)}
                    {batchResults.length > 0 && <>
                      <th className="text-left px-3 py-2 text-gray-500 font-medium">Score</th>
                      <th className="text-left px-3 py-2 text-gray-500 font-medium">Yield</th>
                      <th className="text-left px-3 py-2 text-gray-500 font-medium">Risk</th>
                    </>}
                  </tr>
                </thead>
                <tbody>
                  {csvData.rows.map((row, i) => {
                    const result = batchResults[i];
                    return (
                      <tr key={i} className="border-t border-gray-100">
                        {csvData.headers.map(h => <td key={h} className="px-3 py-2 text-gray-700">{row[h] ?? ""}</td>)}
                        {batchResults.length > 0 && (
                          result?.status === "ok"
                            ? <>
                                <td className="px-3 py-2 font-semibold" style={{ color: result.suitability_score >= 75 ? "#16a34a" : result.suitability_score >= 55 ? "#d97706" : "#dc2626" }}>{result.suitability_score}%</td>
                                <td className="px-3 py-2 text-gray-700">{result.yield_prediction_t_ha} t/ha</td>
                                <td className="px-3 py-2">
                                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${result.risk_level === "Low" ? "bg-green-100 text-green-800" : result.risk_level === "Medium" ? "bg-amber-100 text-amber-800" : "bg-red-100 text-red-800"}`}>{result.risk_level}</span>
                                </td>
                              </>
                            : <td colSpan={3} className="px-3 py-2 text-red-500 text-[10px]">⚠️ {result?.error ?? "Pending"}</td>
                        )}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {batchResults.length > 0 && !batchRunning && (
              <div className="mt-3 flex justify-end">
                <button onClick={downloadBatchCSV} className="text-xs text-green-700 hover:text-green-900 border border-green-200 rounded-lg px-3 py-1.5 hover:bg-green-50 transition-colors">
                  ⬇️ Download batch results (.csv)
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── TIPS ────────────────────────────────────────────────────────── */}
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
        <div className="text-xs font-semibold text-gray-600 mb-2">💡 CSV Format Tips</div>
        <ul className="text-xs text-gray-500 space-y-1">
          <li>• Required columns: <code className="bg-gray-100 px-1 rounded">district</code>, <code className="bg-gray-100 px-1 rounded">crop</code></li>
          <li>• Optional: <code className="bg-gray-100 px-1 rounded">variety</code> — defaults to first variety for that crop</li>
          <li>• District names must match exactly (e.g. Musanze, Rubavu, Huye)</li>
          <li>• Crops: potato, maize, bean, coffee, tea, banana</li>
          <li>• Download the template above to get started quickly</li>
        </ul>
      </div>
    </div>
  );
}
