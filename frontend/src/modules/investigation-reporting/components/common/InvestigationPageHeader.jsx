import { RefreshCw } from "lucide-react";

export default function InvestigationPageHeader({ title, description, eyebrow = "Investigation & Reporting", actions, onRefresh, loading = false }) {
  return <header className="ir-page-header"><div><span className="ir-eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div><div className="ir-header-actions">{onRefresh && <button className="ir-button ir-button--secondary" type="button" onClick={onRefresh} disabled={loading}><RefreshCw size={16}/> Refresh</button>}{actions}</div></header>;
}
