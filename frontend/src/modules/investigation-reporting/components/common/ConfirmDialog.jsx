import { AlertTriangle, X } from "lucide-react";

export default function ConfirmDialog({ open, title, message, confirmLabel = "Confirm", busy = false, onCancel, onConfirm }) {
  if (!open) return null;
  return <div className="ir-confirm-backdrop" onMouseDown={(e) => e.target === e.currentTarget && !busy && onCancel?.()}><section className="ir-confirm" role="alertdialog" aria-modal="true"><button className="ir-confirm__close" onClick={onCancel} disabled={busy} aria-label="Close"><X size={18}/></button><span className="ir-confirm__icon"><AlertTriangle size={20}/></span><h2>{title}</h2><p>{message}</p><footer><button className="ir-button ir-button--secondary" onClick={onCancel} disabled={busy}>Cancel</button><button className="ir-button ir-button--danger" onClick={onConfirm} disabled={busy}>{busy ? "Working…" : confirmLabel}</button></footer></section></div>;
}
