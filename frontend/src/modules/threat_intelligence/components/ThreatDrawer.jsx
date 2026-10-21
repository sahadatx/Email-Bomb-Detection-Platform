import { useEffect } from "react";
import { X } from "lucide-react";

export default function ThreatDrawer({
  open,
  title,
  subtitle,
  children,
  footer,
  onClose,
  dirty = false,
  busy = false,
  back,
}) {
  useEffect(() => {
    if (!open) return undefined;
    const key = (event) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, [open, onClose]);
  if (!open) return null;
  function requestClose() {
    if (busy) return;
    if (dirty && !window.confirm("Discard unsaved changes?")) return;
    onClose();
  }
  return (
    <div
      className="ti-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) requestClose();
      }}
    >
      <aside
        className="ti-drawer"
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <header className="ti-drawer-head">
          {back && (
            <button type="button" className="ti-text-button" onClick={back}>
              ← Back
            </button>
          )}
          <div>
            <h2>{title}</h2>
            {subtitle && <p>{subtitle}</p>}
          </div>
          <button
            type="button"
            className="ti-icon-button"
            onClick={requestClose}
            aria-label="Close drawer"
          >
            <X size={19} />
          </button>
        </header>
        <div className="ti-drawer-body">{children}</div>
        {footer && <footer className="ti-drawer-footer">{footer}</footer>}
      </aside>
    </div>
  );
}
