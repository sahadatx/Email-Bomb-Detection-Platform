import { ArrowUpRight, Cpu, ScanLine, Settings, Shield } from "lucide-react";
import { Link } from "react-router-dom";
import { QUICK_ACTIONS } from "../utils/dashboardConstants";

const icons = { scan: ScanLine, shield: Shield, cpu: Cpu, settings: Settings };
export default function DashboardQuickActions() {
  return (
    <section className="dashboard-quick-actions">
      <div className="dashboard-panel-heading">
        <div>
          <span className="dashboard-panel-kicker">Workspaces</span>
          <h2>Quick actions</h2>
        </div>
      </div>
      <div className="dashboard-action-grid">
        {QUICK_ACTIONS.map((action) => {
          const Icon = icons[action.icon];
          return (
            <Link
              className="dashboard-action-card"
              to={action.to}
              key={action.to}
            >
              <span>
                <Icon size={17} />
              </span>
              <strong>{action.label}</strong>
              <small>{action.description}</small>
              <ArrowUpRight size={15} className="dashboard-action-arrow" />
            </Link>
          );
        })}
      </div>
    </section>
  );
}
