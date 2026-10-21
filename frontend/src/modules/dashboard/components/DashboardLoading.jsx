export default function DashboardLoading() {
  return (
    <div
      className="dashboard-loading"
      aria-label="Loading dashboard"
      aria-busy="true"
    >
      <div className="dashboard-loading-kpis">
        {Array.from({ length: 4 }, (_, index) => (
          <div
            className="dashboard-skeleton dashboard-skeleton-card"
            key={index}
          />
        ))}
      </div>
      <div className="dashboard-loading-panels">
        <div className="dashboard-skeleton dashboard-skeleton-panel" />
        <div className="dashboard-skeleton dashboard-skeleton-panel" />
      </div>
    </div>
  );
}
