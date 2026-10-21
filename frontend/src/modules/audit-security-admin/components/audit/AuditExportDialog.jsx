import { useEffect, useState } from "react";
import RightDrawer from "../common/RightDrawer";

export default function AuditExportDialog({ open, filters, onClose, onExport, loading }) {
  const [format, setFormat] = useState("csv");
  const [limit, setLimit] = useState(1000);
  const [fromDate, setFromDate] = useState(filters?.from_date || "");
  const [toDate, setToDate] = useState(filters?.to_date || "");
  useEffect(() => { if (open) { setFromDate(filters?.from_date || ""); setToDate(filters?.to_date || ""); } }, [open, filters?.from_date, filters?.to_date]);
  return <RightDrawer open={open} title="Export audit logs" description="Choose the output format, date range and maximum records." onClose={onClose} footer={<><button className="asa-button asa-button--secondary" onClick={onClose} disabled={loading}>Cancel</button><button className="asa-button asa-button--primary" onClick={() => onExport({ ...filters, from_date: fromDate, to_date: toDate, format, limit })} disabled={loading || (fromDate && toDate && fromDate > toDate)}>{loading ? "Preparing…" : "Download export"}</button></>}><div className="asa-form"><label>Format<select value={format} onChange={(event) => setFormat(event.target.value)}><option value="csv">CSV</option><option value="json">JSON</option></select></label><label>From<input type="date" value={fromDate} onChange={(event) => setFromDate(event.target.value)}/></label><label>To<input type="date" min={fromDate || undefined} value={toDate} onChange={(event) => setToDate(event.target.value)}/></label><label>Maximum records<input type="number" min="1" max="10000" value={limit} onChange={(event) => setLimit(Number(event.target.value))}/></label><p>Export limit: up to 10,000 records. Sensitive metadata is redacted.</p></div></RightDrawer>;
}
