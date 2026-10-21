import { Cpu } from "lucide-react";
import { Link } from "react-router-dom";
import { statusLabel } from "../utils/dashboardFormatters";

export default function ModelStatus({ data }) {
  return (
    <section className="dashboard-panel dashboard-compact-status">
      <div className="dashboard-panel-heading">
        <div>
          <span className="dashboard-panel-kicker">Inference readiness</span>
          <h2>Active model</h2>
        </div>
        <Cpu size={18} />
      </div>
      <div className="dashboard-model-summary">
        <span
          className={`dashboard-status-dot is-${data?.status || "unknown"}`}
        />
        <strong>{statusLabel(data?.status)}</strong>
        <small>{data?.active_count || 0} active model version(s)</small>
      </div>
      {data?.active_models?.length ? (
        data.active_models.map((model) => (
          <div className="dashboard-model-row" key={model.model_version_id}>
            <strong>{model.name}</strong>
            <span>
              {model.algorithm} · v{model.version}
            </span>
            {!model.artifact_available && (
              <small>Model artifact is unavailable.</small>
            )}
          </div>
        ))
      ) : (
        <p className="dashboard-muted">
          No active model version is registered.
        </p>
      )}
      <Link className="dashboard-text-link" to="/ml-models/registry">
        Open model registry →
      </Link>
    </section>
  );
}
