import { useState } from "react";
import { createPortal } from "react-dom";
import { Eye, MoreVertical, Pencil, Power } from "lucide-react";
import StatusBadge from "../common/StatusBadge";
import { displayDate } from "../../types";

export default function MonitoringRuleTable({ items = [], canManage, onView, onEdit, onToggleStatus }) {
  const [openMenu, setOpenMenu] = useState(null);
  const [menuPosition, setMenuPosition] = useState(null);
  function toggleMenu(event, ruleId) {
    if (openMenu === ruleId) { setOpenMenu(null); return; }
    const rect = event.currentTarget.getBoundingClientRect();
    setMenuPosition({ top: Math.min(rect.bottom + 4, window.innerHeight - 130), right: Math.max(8, window.innerWidth - rect.right) });
    setOpenMenu(ruleId);
  }
  function closeMenu() { setOpenMenu(null); }

  return <div className="asa-table-scroll"><table className="asa-table"><thead><tr><th>Rule Name</th><th>Event Type</th><th>Severity</th><th>Condition</th><th>Status</th><th>Updated By / At</th><th>Action</th></tr></thead><tbody>{items.map((rule) => <tr key={rule.id}><td><strong>{rule.name}</strong><small>{rule.description || "No description"}</small></td><td>{rule.event_type}</td><td><StatusBadge status={rule.severity}/></td><td><code>{rule.condition?.field ? `${rule.condition.field} ${rule.condition.operator} ${rule.condition.value}` : "—"}</code></td><td><StatusBadge status={rule.enabled ? "enabled" : "disabled"}/></td><td>{rule.updated_by_name || "System"}<small>{displayDate(rule.updated_at)}</small></td><td><div className="asa-rule-actions"><button className="asa-rule-menu-trigger" aria-label={`Actions for ${rule.name}`} aria-haspopup="menu" aria-expanded={openMenu === rule.id} onClick={(event) => toggleMenu(event, rule.id)}><MoreVertical size={17}/></button>{openMenu === rule.id && createPortal(<><button className="asa-rule-menu-dismiss" aria-label="Close actions menu" onClick={closeMenu}/><div className="asa-rule-menu asa-rule-menu--portal" style={menuPosition} role="menu"><button role="menuitem" onClick={() => { closeMenu(); onView(rule); }}><Eye size={14}/> View details</button><button role="menuitem" disabled={!canManage} onClick={() => { closeMenu(); onEdit(rule); }}><Pencil size={14}/> Edit</button><button role="menuitem" disabled={!canManage} onClick={() => { closeMenu(); onToggleStatus(rule); }}><Power size={14}/> {rule.enabled ? "Disable rule" : "Enable rule"}</button></div></>, document.body)}</div></td></tr>)}</tbody></table></div>;
}
