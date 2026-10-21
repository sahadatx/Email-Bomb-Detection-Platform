import { useEffect } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

export default function RightDrawer({ open, title, description, onClose, children, footer, wide = false }) {
  useEffect(() => {
    if (!open) return undefined;
    const oldOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const keydown = (event) => event.key === "Escape" && onClose?.();
    window.addEventListener("keydown", keydown);
    return () => {
      document.body.style.overflow = oldOverflow;
      window.removeEventListener("keydown", keydown);
    };
  }, [open, onClose]);

  if (!open) return null;
  return createPortal(
    <div className="ir-overlay" onMouseDown={(event) => event.target === event.currentTarget && onClose?.()}>
      <aside className={`ir-drawer${wide ? " ir-drawer--wide" : ""}`} role="dialog" aria-modal="true" aria-label={title}>
        <header className="ir-drawer__header">
          <div><h2>{title}</h2>{description && <p>{description}</p>}</div>
          <button className="ir-icon-button" type="button" onClick={onClose} aria-label="Close drawer"><X size={19} /></button>
        </header>
        <div className="ir-drawer__body">{children}</div>
        {footer && <footer className="ir-drawer__footer">{footer}</footer>}
      </aside>
    </div>, document.body,
  );
}
