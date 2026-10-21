import { FlaskConical, RefreshCw } from "lucide-react";

export default function ExperimentPageHeader({ onRefresh, onCreate, loading = false, canManage = false }) {
  return <header className="ex-page-header"><div><span className="ex-eyebrow">ANALYTICS / EXPERIMENTS</span><h1>Experiments</h1><p>Create, manage and compare model training and evaluation runs.</p></div><div className="ex-header-actions"><button className="ex-button ex-button--secondary" onClick={onRefresh} disabled={loading}><RefreshCw size={15}/> Refresh</button>{canManage && <button type="button" className="ex-button ex-button--primary" onClick={onCreate}><FlaskConical size={15}/> New Experiment</button>}</div></header>;
}
