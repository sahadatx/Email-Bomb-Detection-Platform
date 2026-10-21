import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { MoreHorizontal } from "lucide-react";

/** Row action menu rendered outside scroll containers so it is never clipped. */
export default function ActionMenu({ label = "Actions", items = [], className = "" }) {
  const triggerRef = useRef(null);
  const menuRef = useRef(null);
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0, ready: false });

  useLayoutEffect(() => {
    if (!open || !triggerRef.current) return undefined;
    const place = () => {
      const rect = triggerRef.current?.getBoundingClientRect();
      if (!rect) return;
      const height = menuRef.current?.offsetHeight || Math.min(280, items.length * 38 + 12);
      const width = menuRef.current?.offsetWidth || 210;
      const top = window.innerHeight - rect.bottom >= height + 8 || rect.top < height + 8
        ? rect.bottom + 5
        : rect.top - height - 5;
      const left = Math.max(8, Math.min(rect.right - width, window.innerWidth - width - 8));
      setPosition({ top, left, ready: true });
    };
    place();
    window.addEventListener("resize", place);
    window.addEventListener("scroll", place, true);
    return () => {
      window.removeEventListener("resize", place);
      window.removeEventListener("scroll", place, true);
    };
  }, [open, items.length]);

  useEffect(() => {
    if (!open) return undefined;
    const dismiss = (event) => {
      if (event.type === "keydown" && event.key === "Escape") setOpen(false);
      if (event.type === "pointerdown" && !menuRef.current?.contains(event.target) && !triggerRef.current?.contains(event.target)) setOpen(false);
    };
    document.addEventListener("pointerdown", dismiss);
    document.addEventListener("keydown", dismiss);
    return () => {
      document.removeEventListener("pointerdown", dismiss);
      document.removeEventListener("keydown", dismiss);
    };
  }, [open]);

  return <>
    <button ref={triggerRef} type="button" className="ir-action-menu-trigger" aria-label={`${label} menu`} aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen((value) => !value)}><MoreHorizontal size={18}/></button>
    {open && createPortal(<div ref={menuRef} className={`ir-action-popover ${className}`.trim()} role="menu" style={{ top: position.top, left: position.left, visibility: position.ready ? "visible" : "hidden" }}>
      {items.map(({ label: itemLabel, icon: Icon, onClick, disabled = false, danger = false }, index) => <button key={`${itemLabel}-${index}`} type="button" role="menuitem" className={danger ? "is-danger" : ""} disabled={disabled} onClick={() => { setOpen(false); onClick?.(); }}>{Icon && <Icon size={14}/>} {itemLabel}</button>)}
    </div>, document.body)}
  </>;
}
