import { Inbox } from "lucide-react";
export default function DashboardEmptyState({
  message = "No records are available for these filters.",
}) {
  return (
    <div className="dashboard-state">
      <span>
        <Inbox size={22} />
      </span>
      <h2>No dashboard data</h2>
      <p>{message}</p>
    </div>
  );
}
