import { useCallback, useEffect, useState } from "react";
import { Activity, AlertTriangle, Eye } from "lucide-react";
import DetectionActivityChart from "../components/DetectionActivityChart";
import DetectionPageShell from "../components/DetectionPageShell";
import DetectionStatCard from "../components/DetectionStatCard";
import { behavioralService } from "../services/behavioralService";
import { detectionService } from "../services/detectionService";

const PERIOD_LABELS = { "24h": "Last 24 hours", "7d": "Last 7 days", "30d": "Last 30 days" };

export default function BehavioralAnalysisPage() {
  const [period, setPeriod] = useState("7d");
  const [summary, setSummary] = useState(null);
  const [activity, setActivity] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadBehavior = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [behaviorSummary, timeline, anomalyRows] = await Promise.all([
        behavioralService.summary(),
        behavioralService.activity(period),
        behavioralService.anomalies(),
      ]);
      setSummary(behaviorSummary);
      setActivity(timeline.activity || []);
      setAnomalies(anomalyRows
        .slice()
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at)));
    } catch (requestError) {
      setError(requestError.message || "Could not load behavioral analysis.");
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => { loadBehavior(); }, [loadBehavior]);

  async function viewDetection(detectionId) {
    try {
      setSelected(await detectionService.detail(detectionId));
    } catch (requestError) {
      setError(requestError.message || "Could not load this detection record.");
    }
  }

  return (
    <DetectionPageShell
      page="behavior"
      title="Behavioral Analysis"
      description="Inspect stored email activity and anomalies found in sender history."
      loading={loading}
      error={error}
      onRefresh={loadBehavior}
      selectedDetection={selected}
      onCloseDetection={() => setSelected(null)}
    >
      <section className="det-stats" aria-label="Behavioral analysis summary">
        <DetectionStatCard icon={Activity} label="Emails Analyzed" value={summary?.emails_analyzed ?? 0} detail="Stored email collection" />
        <DetectionStatCard icon={AlertTriangle} label="Anomalies" value={summary?.anomalies ?? 0} tone="amber" detail="Persisted behavioral findings" />
      </section>

      <section className="det-panel">
        <header>
          <div>
            <h2>Email Activity Over Time</h2>
            <p>{PERIOD_LABELS[period]} · timestamp counts from the email collection.</p>
          </div>
          <label className="det-period-select">
            <span>Period</span>
            <select value={period} onChange={(event) => setPeriod(event.target.value)}>
              {Object.entries(PERIOD_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
        </header>
        <DetectionActivityChart points={activity} valueKey="emails" valueLabel="emails" />
      </section>

      <section className="det-panel">
        <header>
          <div>
            <h2>Detected Behavior Patterns</h2>
            <p>Anomalies returned from saved behavioral analysis results.</p>
          </div>
          <span>{anomalies.length} findings</span>
        </header>
        {anomalies.length ? (
          <div className="det-anomaly-table-wrap">
            <table className="det-table det-anomaly-table">
              <thead><tr><th>Pattern</th><th>Severity</th><th>Sender</th><th>Subject</th><th>Detected</th><th>Evidence</th></tr></thead>
              <tbody>
                {anomalies.map((anomaly, index) => (
                  <tr key={`${anomaly.detection_id}-${anomaly.pattern}-${index}`}>
                    <td><strong>{anomaly.pattern.replaceAll("_", " ")}</strong><small>{anomaly.description}</small></td>
                    <td><span className={`det-severity ${anomaly.severity}`}>{anomaly.severity}</span></td>
                    <td>{anomaly.sender || "Unavailable"}</td>
                    <td>{anomaly.subject || "—"}</td>
                    <td>{anomaly.created_at ? new Date(anomaly.created_at).toLocaleString() : "—"}</td>
                    <td><button className="det-icon-btn" title="View detection evidence" onClick={() => viewDetection(anomaly.detection_id)}><Eye size={16}/></button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="det-empty">
            <strong>Insufficient behavioral history</strong>
            <span>The backend needs enough sender history before it can report patterns.</span>
          </div>
        )}
      </section>
    </DetectionPageShell>
  );
}
