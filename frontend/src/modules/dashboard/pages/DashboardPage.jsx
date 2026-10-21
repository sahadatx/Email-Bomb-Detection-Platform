import { useMemo } from "react";
import DashboardHeader from "../components/DashboardHeader";
import DashboardFilters from "../components/DashboardFilters";
import DashboardSummaryCards from "../components/DashboardSummaryCards";
import DetectionOverview from "../components/DetectionOverview";
import ClassificationChart from "../components/ClassificationChart";
import RiskDistributionChart from "../components/RiskDistributionChart";
import EmailActivityChart from "../components/EmailActivityChart";
import RecentDetections from "../components/RecentDetections";
import SystemHealth from "../components/SystemHealth";
import ModelStatus from "../components/ModelStatus";
import ThreatFeedStatus from "../components/ThreatFeedStatus";
import RecentActivity from "../components/RecentActivity";
import DashboardQuickActions from "../components/DashboardQuickActions";
import DashboardLoading from "../components/DashboardLoading";
import DashboardEmptyState from "../components/DashboardEmptyState";
import DashboardErrorState from "../components/DashboardErrorState";
import useDashboardFilters from "../hooks/useDashboardFilters";
import useDashboard from "../hooks/useDashboard";
import useDashboardRefresh from "../hooks/useDashboardRefresh";
import { formatDate } from "../utils/dashboardFormatters";
import "../styles/dashboard.css";

export default function DashboardPage() {
  const { filters, queryFilters, updateFilter, resetFilters, ready } =
    useDashboardFilters();
  const stableFilters = useMemo(() => queryFilters, [queryFilters]);
  const { data, loading, error, refresh } = useDashboard(stableFilters, ready);
  useDashboardRefresh(refresh);

  return (
    <main className="dashboard-page">
      <DashboardHeader data={data} loading={loading} onRefresh={refresh} />
      <DashboardFilters
        filters={filters}
        modelOptions={data?.model_options}
        onChange={updateFilter}
        onReset={resetFilters}
      />
      {error ? (
        <DashboardErrorState error={error} onRetry={refresh} />
      ) : !ready ? (
        <DashboardEmptyState message="Select both the start and end dates to view this custom range." />
      ) : loading && !data ? (
        <DashboardLoading />
      ) : data ? (
        <>
          <section className="dashboard-section">
            <div className="dashboard-section-heading">
              <div>
                <span>Operational overview</span>
                <h2>Threat monitoring</h2>
              </div>
              <small>Data as of {formatDate(data.generated_at)}</small>
            </div>
            <DashboardSummaryCards summary={data.summary} />
          </section>
          <section className="dashboard-overview-grid">
            <DetectionOverview items={data.classification} />
            <div className="dashboard-panel">
              <div className="dashboard-panel-heading">
                <div>
                  <span className="dashboard-panel-kicker">Classification</span>
                  <h2>Detection mix</h2>
                </div>
              </div>
              <ClassificationChart items={data.classification} />
            </div>
            <RiskDistributionChart items={data.risk_distribution} />
          </section>
          <section className="dashboard-panel dashboard-activity-panel">
            <div className="dashboard-panel-heading">
              <div>
                <span className="dashboard-panel-kicker">Email activity</span>
                <h2>Volume and classification trends</h2>
                <p>
                  Based on completed detection records for the selected period.
                </p>
              </div>
              <span className="dashboard-range-label">
                {filters.time_range === "custom"
                  ? "Custom range"
                  : `Last ${filters.time_range}`}
              </span>
            </div>
            <EmailActivityChart items={data.activity} />
          </section>
          <RecentDetections items={data.recent_detections} />
          <section className="dashboard-lower-grid">
            <SystemHealth health={data.system_health} />
            <div className="dashboard-status-stack">
              <ModelStatus data={data.model_status} />
              <ThreatFeedStatus data={data.threat_feed_status} />
            </div>
            <RecentActivity items={data.recent_activity} />
          </section>
          <DashboardQuickActions />
          {loading && (
            <div className="dashboard-refresh-note" role="status">
              Updating dashboard…
            </div>
          )}
        </>
      ) : (
        <DashboardEmptyState />
      )}
    </main>
  );
}
