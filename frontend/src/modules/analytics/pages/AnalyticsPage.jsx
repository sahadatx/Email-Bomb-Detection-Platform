import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../../../core/auth/AuthProvider";
import AnalyticsPageHeader from "../components/AnalyticsPageHeader";
import AnalyticsFilters from "../components/AnalyticsFilters";
import AnalyticsSummaryCards from "../components/AnalyticsSummaryCards";
import ClassificationTrends from "../components/ClassificationTrends";
import ClassificationDistribution from "../components/ClassificationDistribution";
import RiskDistribution from "../components/RiskDistribution";
import DetectionPerformance from "../components/DetectionPerformance";
import BehavioralAnalytics from "../components/BehavioralAnalytics";
import RecentDetectionAnalytics from "../components/RecentDetectionAnalytics";
import { useAnalytics } from "../hooks/useAnalytics";
import { useAnalyticsFilters } from "../hooks/useAnalyticsFilters";
import { analyticsService } from "../services/analyticsService";
import "../styles/analytics.css";

export default function AnalyticsPage() {
  const { user } = useAuth();
  const { filters, requestFilters, update, reset } = useAnalyticsFilters();
  const { data, loading, error, refresh } = useAnalytics(requestFilters);
  const [models, setModels] = useState([]);
  const [modelsError, setModelsError] = useState("");
  const [exporting, setExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState("csv");
  const [exportLimit, setExportLimit] = useState("1000");
  const [exportError, setExportError] = useState("");
  const [toast, setToast] = useState("");
  const canExport = ["ADMIN", "SECURITY_ANALYST"].includes(user?.role);
  useEffect(() => { let active = true; analyticsService.models().then((result) => { if (active) setModels(result.items || []); }).catch((cause) => { if (active) setModelsError(cause.message || "Could not load model filter options."); }); return () => { active = false; }; }, []);
  const filterQuery = useMemo(() => requestFilters || {}, [requestFilters]);
  async function exportCurrent() {
    if (!canExport || !requestFilters || exporting) return;
    setExporting(true); setExportError("");
    try { await analyticsService.export({ ...filterQuery, format: exportFormat, limit: exportLimit }); setToast("Analytics export downloaded."); }
    catch (cause) { setExportError(cause.message || "Could not export analytics."); }
    finally { setExporting(false); }
  }

  return <main className="an-page">
    <AnalyticsPageHeader onRefresh={refresh} onExport={exportCurrent} exporting={exporting} loading={loading} canExport={canExport && Boolean(requestFilters)} format={exportFormat} onFormatChange={setExportFormat} limit={exportLimit} onLimitChange={setExportLimit}/>
    <AnalyticsFilters filters={filters} models={models} update={update} reset={reset} disabled={loading}/>
    {modelsError && <div className="an-inline-warning" role="status">{modelsError} · Model filtering is unavailable.</div>}
    {exportError && <div className="an-inline-error" role="alert">{exportError}</div>}
    {error ? <div className="an-state an-state--error" role="alert"><strong>Analytics could not be loaded</strong><span>{error}</span><button className="an-button an-button--secondary" onClick={refresh}>Retry</button></div> : !requestFilters ? <div className="an-state"><strong>Select a complete custom date range</strong><span>Analytics refreshes automatically when both dates are selected.</span></div> : <>
      {toast && <div className="an-toast" role="status">{toast}<button onClick={() => setToast("")}>Dismiss</button></div>}
      <AnalyticsSummaryCards data={data.overview} loading={loading}/>
      <div className="an-grid an-grid--wide"><ClassificationTrends items={data.classification?.items}/><ClassificationDistribution items={data.classification?.distribution}/></div>
      <div className="an-grid"><RiskDistribution items={data.risk?.items}/><DetectionPerformance data={data.performance}/></div>
      <div className="an-grid"><BehavioralAnalytics data={data.behavior}/><section className="an-panel an-source-panel"><h2>Data and metric definitions</h2><p>Analytics uses completed detection records and stored risk or behavioral assessments. Model metrics come from completed ML evaluations; the card currently uses the latest Validation evaluation in the selected period.</p><small>{data.overview?.total_detections?.toLocaleString?.() ?? 0} completed detections · Sources: {data.overview?.data_sources?.join(", ") || "waiting for API data"}</small></section></div>
      <RecentDetectionAnalytics items={data.recent}/>
    </>}
  </main>;
}
