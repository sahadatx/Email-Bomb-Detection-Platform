import { useCallback, useEffect, useState } from "react";
import { Activity, AlertTriangle, CheckCircle2, ShieldAlert } from "lucide-react";
import DetectionActivityChart from "../components/DetectionActivityChart";
import DetectionPageShell from "../components/DetectionPageShell";
import DetectionResultsTable from "../components/DetectionResultsTable";
import DetectionStatCard from "../components/DetectionStatCard";
import { detectionService } from "../services/detectionService";

export default function DetectionOverviewPage() {
  const [summary, setSummary] = useState(null);
  const [recent, setRecent] = useState([]);
  const [modelAvailable, setModelAvailable] = useState(false);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadOverview = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [overview, detections, activeModel] = await Promise.all([
        detectionService.overview(),
        detectionService.list({ page: 1, page_size: 8 }),
        detectionService.activeModel(),
      ]);
      setSummary(overview);
      setRecent(detections.items || []);
      setModelAvailable(Boolean(activeModel.available));
    } catch (requestError) {
      setError(requestError.message || "Could not load the detection overview.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadOverview(); }, [loadOverview]);

  return (
    <DetectionPageShell
      page="overview"
      title="Detection Overview"
      description="Monitor email detection and risk activity."
      loading={loading}
      error={error}
      onRefresh={loadOverview}
      selectedDetection={selected}
      onCloseDetection={() => setSelected(null)}
    >
      <div className={`det-system-state ${modelAvailable ? "ready" : "unavailable"}`}>
        <span />
        {modelAvailable
          ? "System Ready · Active model available"
          : "System Unavailable · Activate a model version to run detections"}
      </div>

      <section className="det-stats" aria-label="Detection summary">
        <DetectionStatCard icon={Activity} label="Total Detections" value={summary?.total_detections ?? 0} />
        <DetectionStatCard icon={ShieldAlert} label="Bomb Detected" value={summary?.bomb_detected ?? 0} tone="red" />
        <DetectionStatCard icon={CheckCircle2} label="Normal Emails" value={summary?.normal_emails ?? 0} tone="green" />
        <DetectionStatCard icon={AlertTriangle} label="High Risk" value={summary?.high_risk ?? 0} tone="amber" />
      </section>

      <section className="det-panel">
        <header>
          <div>
            <h2>Detection Activity</h2>
            <p>Saved detections grouped by UTC date for the selected period.</p>
          </div>
        </header>
        <DetectionActivityChart points={summary?.activity || []} />
      </section>

      <section className="det-panel">
        <header>
          <div>
            <h2>Recent Detections</h2>
            <p>The latest saved predictions and risk assessments.</p>
          </div>
          <span>{recent.length} shown</span>
        </header>
        <DetectionResultsTable
          items={recent}
          onView={setSelected}
          emptyTitle="No detections yet"
          emptyDescription="Run a detection to populate this recent activity list."
        />
      </section>
    </DetectionPageShell>
  );
}
