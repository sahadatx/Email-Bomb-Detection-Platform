import { RefreshCw } from "lucide-react";

export default function AdminPageHeader({ eyebrow = "AUDIT & ADMIN", title, description, onRefresh, loading = false, actions }) {
  return <header className="asa-page-header"><div><span className="asa-eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div><div className="asa-header-actions">{actions}<button className="asa-button asa-button--secondary" onClick={onRefresh} disabled={loading}><RefreshCw size={15} className={loading ? "asa-spin" : ""}/> Refresh</button></div></header>;
}
