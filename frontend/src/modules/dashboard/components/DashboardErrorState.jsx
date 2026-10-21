import { AlertCircle, RefreshCw } from "lucide-react";
export default function DashboardErrorState({ error, onRetry }) {
  return (
    <div className="dashboard-state dashboard-error-state">
      <span>
        <AlertCircle size={22} />
      </span>
      <h2>Dashboard data could not be loaded</h2>
      <p>{error || "The dashboard API returned an error."}</p>
      <button
        type="button"
        className="dashboard-button dashboard-button-primary"
        onClick={onRetry}
      >
        <RefreshCw size={15} /> Try again
      </button>
    </div>
  );
}
