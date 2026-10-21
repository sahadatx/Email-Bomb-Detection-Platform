import RightDrawer from "./RightDrawer";

export default function FilterDrawer({ open, title = "Filters", description = "Narrow the records shown in this workspace.", onClose, onApply, onClear, children, busy = false }) {
  return <RightDrawer open={open} title={title} description={description} onClose={onClose} footer={<><button className="ir-button ir-button--secondary" type="button" onClick={onClose} disabled={busy}>Cancel</button><button className="ir-button ir-button--quiet" type="button" onClick={onClear} disabled={busy}>Clear All</button><button className="ir-button ir-button--primary" type="button" onClick={onApply} disabled={busy}>Apply Filters</button></>}><div className="ir-form">{children}</div></RightDrawer>;
}
