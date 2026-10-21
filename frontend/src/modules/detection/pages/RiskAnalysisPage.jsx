import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, ShieldAlert, ShieldCheck } from "lucide-react";
import DetectionPageShell from "../components/DetectionPageShell";
import DetectionResultsTable from "../components/DetectionResultsTable";
import DetectionStatCard from "../components/DetectionStatCard";
import RiskDistributionChart from "../components/RiskDistributionChart";
import { detectionService } from "../services/detectionService";
import { riskService } from "../services/riskService";

export default function RiskAnalysisPage() {
  const [summary, setSummary] = useState(null);
  const [records, setRecords] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadRiskAnalysis = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [risk, highRisk, criticalRisk] = await Promise.all([
        riskService.summary(),
        detectionService.list({ page: 1, page_size: 100, risk_level: "high" }),
        detectionService.list({ page: 1, page_size: 100, risk_level: "critical" }),
      ]);
      setSummary(risk);
      setRecords([...criticalRisk.items, ...highRisk.items]
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at)));
    } catch (requestError) {
      setError(requestError.message || "Could not load risk analysis.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadRiskAnalysis(); }, [loadRiskAnalysis]);

  const counts = summary?.distribution || {};
  const factorCount = summary?.factors?.length || 0;

  return (
    <DetectionPageShell
      page="risk"
      title="Risk Analysis"
      description="Review persisted risk scores, severity distribution, and the factors behind each assessment."
      loading={loading}
      error={error}
      onRefresh={loadRiskAnalysis}
      selectedDetection={selected}
      onCloseDetection={() => setSelected(null)}
    >
      <section className="det-stats risk-stats" aria-label="Risk counts">
        <DetectionStatCard icon={AlertTriangle} label="Critical Risk" value={counts.critical ?? 0} tone="critical" />
        <DetectionStatCard icon={ShieldAlert} label="High Risk" value={counts.high ?? 0} tone="high" />
        <DetectionStatCard icon={AlertTriangle} label="Medium Risk" value={counts.medium ?? 0} tone="medium" />
        <DetectionStatCard icon={ShieldCheck} label="Low Risk" value={counts.low ?? 0} tone="low" />
      </section>

      <div className="det-risk-layout">
        <section className="det-panel">
          <header>
            <div>
              <h2>Risk Distribution</h2>
              <p>Counts are returned by the risk assessment API.</p>
            </div>
          </header>
          <RiskDistributionChart distribution={counts} />
        </section>

        <section className="det-panel">
          <header>
            <div>
              <h2>Risk Factors</h2>
              <p>Factors recorded with completed risk assessments.</p>
            </div>
            <span>{factorCount} factor types</span>
          </header>
          {factorCount ? (
            <div className="det-factor-list">
              {summary.factors.map((factor) => (
                <article className="det-factor-card" key={factor.name}>
                  <div>
                    <strong>{factor.name}</strong>
                    <span>{factor.occurrences} {factor.occurrences === 1 ? "record" : "records"}</span>
                  </div>
                  <b className={`risk-${String(factor.impact || "unknown").toLowerCase()}`}>{factor.impact || "Unspecified"}</b>
                </article>
              ))}
            </div>
          ) : (
            <div className="det-empty">Risk factors will appear after an assessment is saved.</div>
          )}
        </section>
      </div>

      <section className="det-panel">
        <header>
          <div>
            <h2>High and Critical Detections</h2>
            <p>Latest high and critical records. Select a row to inspect its evidence.</p>
          </div>
          <span>{records.length} shown · maximum 200</span>
        </header>
        <DetectionResultsTable
          items={records}
          onView={setSelected}
          emptyTitle="No high or critical detections"
          emptyDescription="Saved high and critical risk assessments will appear here."
        />
      </section>
    </DetectionPageShell>
  );
}
