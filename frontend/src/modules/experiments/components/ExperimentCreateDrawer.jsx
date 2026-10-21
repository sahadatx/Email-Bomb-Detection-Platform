import { useEffect } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import ExperimentForm from "./ExperimentForm";

export default function ExperimentCreateDrawer({ open, onClose }) {
  useEffect(() => {
    if (!open) return undefined;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const handleKeyDown = (event) => { if (event.key === "Escape") onClose(); };
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, onClose]);

  if (!open) return null;
  return createPortal(<div className="ex-drawer-overlay" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
    <aside className="ex-drawer" role="dialog" aria-modal="true" aria-labelledby="ex-drawer-title">
      <header className="ex-drawer-header"><div><span className="ex-eyebrow">ANALYTICS / EXPERIMENTS</span><h2 id="ex-drawer-title">New Experiment</h2><p>Configure the model, dataset and training options.</p></div><button type="button" className="ex-drawer-close" onClick={onClose} aria-label="Close new experiment"><X size={19}/></button></header>
      <div className="ex-drawer-body"><ExperimentForm inDrawer onClose={onClose}/></div>
    </aside>
  </div>, document.body);
}
