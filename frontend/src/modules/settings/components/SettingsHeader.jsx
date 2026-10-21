import { ShieldCheck } from "lucide-react";

export default function SettingsHeader({ title, description, connectionState = "loading" }) {
  const status = {
    loading: "Loading live settings",
    connected: "Live settings loaded",
    unavailable: "Settings unavailable",
  }[connectionState];
  return <header className="settings-header"><div><span className="settings-eyebrow"><ShieldCheck size={14} /> System</span><h1>{title || "Settings"}</h1><p>{description || "Configure supported platform behavior."}</p></div><span className={`settings-readonly-pill is-${connectionState}`} role="status">{status}</span></header>;
}
