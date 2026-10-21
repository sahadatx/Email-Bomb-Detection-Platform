import { REPORT_SECTIONS } from "../../types";
export default function ReportSectionsSelector({ selected = [], onChange }) {
  return <fieldset className="ir-fieldset"><legend>Report Sections *</legend><div className="ir-section-grid">{REPORT_SECTIONS.map(([key, label]) => <label className="ir-check-row" key={key}><input type="checkbox" checked={selected.includes(key)} onChange={() => onChange(selected.includes(key) ? selected.filter((item) => item !== key) : [...selected, key])}/><span>{label}</span></label>)}</div></fieldset>;
}
