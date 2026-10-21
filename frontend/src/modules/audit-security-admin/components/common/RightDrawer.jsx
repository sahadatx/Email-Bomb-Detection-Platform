import { useEffect } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

export default function RightDrawer({ open, title, description, onClose, children, footer, wide = false }) {
  useEffect(() => {
    if (!open) return undefined;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const keydown = (event) => event.key === "Escape" && onClose?.();
    window.addEventListener("keydown", keydown);
    return () => { document.body.style.overflow = previous; window.removeEventListener("keydown", keydown); };
  }, [open, onClose]);
  if (!open) return null;
  return createPortal(<><button className="asa-drawer-backdrop" aria-label="Close drawer" onClick={onClose}/><aside className={`asa-drawer${wide ? " asa-drawer--wide" : ""}`} role="dialog" aria-modal="true" aria-label={title}><header><div><h2>{title}</h2>{description && <p>{description}</p>}</div><button aria-label="Close" onClick={onClose}><X size={19}/></button></header><div className="asa-drawer-body">{children}</div>{footer && <footer>{footer}</footer>}</aside></>, document.body);
}
