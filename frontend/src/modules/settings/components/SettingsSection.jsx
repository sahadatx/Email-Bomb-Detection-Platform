import { AlertCircle, Check, Info } from "lucide-react";

function SettingControl({ field, value, onChange, disabled, id }) {
  if (field.value_type === "boolean") {
    return <button id={id} type="button" className={`settings-switch${value ? " is-on" : ""}`} role="switch" aria-label={field.label} aria-checked={Boolean(value)} disabled={disabled} onClick={() => onChange(!value)}><i /></button>;
  }
  if (field.value_type === "model_version") {
    return <select id={id} value={value || ""} disabled={disabled} onChange={(event) => onChange(event.target.value || null)}><option value="">Use latest active version automatically</option>{field.options.map((option) => <option value={option.value} key={option.value}>{option.label}</option>)}</select>;
  }
  if (field.value_type === "status") {
    return <span className={`settings-value-badge is-${value}`}><i />{String(value || "Unknown").replaceAll("_", " ")}</span>;
  }
  return <input id={id} type={field.value_type === "integer" || field.value_type === "threshold" ? "number" : "text"} min={field.value_type === "threshold" ? 1 : field.value_type === "integer" ? 1 : undefined} max={field.value_type === "threshold" ? 100 : undefined} step={field.value_type === "threshold" ? 1 : undefined} value={value ?? ""} disabled={disabled} onChange={(event) => onChange(field.value_type === "integer" || field.value_type === "threshold" ? (event.target.value === "" ? "" : Number(event.target.value)) : event.target.value)} />;
}

export default function SettingsSection({ category, values, onChange, disabled }) {
  return <section className="settings-section" aria-labelledby="settings-section-title"><div className="settings-section-heading"><div><span>Configuration</span><h2 id="settings-section-title">{category.title}</h2><p>{category.description}</p></div><span className={`settings-supported${category.supported ? "" : " is-unavailable"}`}>{category.supported ? <Check size={13} /> : <AlertCircle size={13} />} {category.supported ? "Available" : "Unavailable"}</span></div>{category.notice && <div className="settings-notice"><Info size={16} /><span>{category.notice}</span></div>}{category.fields.length ? <div className="settings-fields">{category.fields.map((field, index) => { const id = `setting-${category.category}-${index}`; return <div className="settings-field" key={field.key}><div className="settings-field-copy"><label htmlFor={id}><strong>{field.label}</strong></label><small>{field.description}</small></div><SettingControl id={id} field={field} value={values[field.key]} onChange={(value) => onChange(field.key, value)} disabled={disabled || !field.editable} /></div>; })}</div> : !category.notice && <div className="settings-empty">No settings are available for this category.</div>}{category.links?.length > 0 && <div className="settings-related-links">{category.links.map((link) => <a href={link.href} key={link.href}>{link.label} →</a>)}</div>}</section>;
}
