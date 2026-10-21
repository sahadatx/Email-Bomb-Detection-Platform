import { Activity, Bell, Cpu, Mail, Radar, Settings2, Shield, SlidersHorizontal, TriangleAlert, Workflow } from "lucide-react";
import { NavLink } from "react-router-dom";
import { CATEGORY_ROUTE, SETTINGS_CATEGORIES } from "../utils/settingsConstants";

const icons = { general: Settings2, detection: Workflow, risk: TriangleAlert, models: Cpu, email_processing: Mail, threat_intelligence: Radar, notifications: Bell, security: Shield };

export default function SettingsSidebar({ categories }) {
  const items = categories?.length ? categories.map((item) => ({ id: item.category, label: item.title, description: item.description, supported: item.supported })) : SETTINGS_CATEGORIES;
  return <nav className="settings-sidebar" aria-label="Settings categories"><div className="settings-sidebar-title"><SlidersHorizontal size={15} /> Categories</div>{items.map((item) => { const Icon = icons[item.id] || SlidersHorizontal; return <NavLink key={item.id} to={CATEGORY_ROUTE(item.id)} className={({ isActive }) => `settings-nav-item${isActive ? " is-active" : ""}`}><Icon size={16} /><span><strong>{item.label}</strong><small>{item.description}</small></span></NavLink>; })}<div className="settings-sidebar-divider" /><NavLink to="/audit" className="settings-nav-item"><Activity size={16} /><span><strong>Audit &amp; Activity</strong><small>Review configuration changes</small></span></NavLink></nav>;
}
