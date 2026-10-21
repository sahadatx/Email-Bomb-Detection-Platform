import RightDrawer from "./RightDrawer";

export default function DetailsDrawer({ open, title, description, onClose, children, footer, wide = true, loading = false, error }) {
  return <RightDrawer open={open} title={title} description={description} onClose={onClose} footer={footer} wide={wide}>{error ? <div className="ir-alert" role="alert">{error}</div> : null}{loading ? <div className="ir-state" role="status">Loading details…</div> : children}</RightDrawer>;
}
