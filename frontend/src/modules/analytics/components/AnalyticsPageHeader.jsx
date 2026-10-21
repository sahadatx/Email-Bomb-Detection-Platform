import { Download, RefreshCw } from "lucide-react";

export default function AnalyticsPageHeader({ onRefresh, onExport, exporting = false, loading = false, canExport = true, format, onFormatChange, limit, onLimitChange }) {
  return <header className="an-page-header">
    <div className="an-header-copy"><span className="an-eyebrow">PLATFORM INSIGHTS</span><h1>Analytics</h1><p>Analyze email security, detection and model performance.</p></div>
    <div className="an-header-actions">
      {canExport && <div className="an-export-toolbar" aria-label="Export analytics">
        <label className="an-export-option"><span>Format</span><select value={format} onChange={(event) => onFormatChange(event.target.value)}><option value="csv">CSV</option><option value="json">JSON</option></select></label>
        <label className="an-export-option"><span>Rows</span><select value={limit} onChange={(event) => onLimitChange(event.target.value)}><option value="1000">1,000</option><option value="5000">5,000</option><option value="10000">10,000</option></select></label>
        <button className="an-button an-button--primary" onClick={onExport} disabled={loading || exporting}><Download size={16}/>{exporting ? "Exporting…" : "Export"}</button>
      </div>}
      <button className="an-button an-button--secondary an-refresh-button" onClick={onRefresh} disabled={loading}><RefreshCw size={16}/> Refresh</button>
    </div>
  </header>;
}
