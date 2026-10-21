import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Eye, MoreVertical, Pencil, RefreshCw } from "lucide-react";
import { displayDate, displayLabel } from "../types/threatIntelligence";

function FeedActionMenu({ feed, canManage, syncDisabled, syncingId, onView, onEdit, onSync }) {
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState(null);
  const triggerRef = useRef(null);
  const menuRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;

    const updatePosition = () => {
      const rect = triggerRef.current?.getBoundingClientRect();
      if (!rect) return;
      const menuHeight = menuRef.current?.getBoundingClientRect().height || 0;
      const belowTop = rect.bottom + 4;
      const top = belowTop + menuHeight <= window.innerHeight - 8
        ? belowTop
        : Math.max(8, rect.top - menuHeight - 4);
      setPosition({
        top,
        right: Math.max(8, window.innerWidth - rect.right),
      });
    };
    const handlePointerDown = (event) => {
      if (!triggerRef.current?.contains(event.target) && !menuRef.current?.contains(event.target)) {
        setOpen(false);
      }
    };
    const handleKeyDown = (event) => {
      if (event.key === "Escape") setOpen(false);
    };

    updatePosition();
    requestAnimationFrame(updatePosition);
    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
    };
  }, [open]);

  const runAction = (action) => {
    setOpen(false);
    action(feed);
  };

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        className={`ti-feed-action-trigger${open ? " is-open" : ""}`}
        aria-label={`Actions for ${feed.name}`}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <MoreVertical size={17} />
      </button>
      {open && position && createPortal(
        <div ref={menuRef} className="ti-feed-action-menu__items" role="menu" style={position}>
          <button role="menuitem" onClick={() => runAction(onView)}>
            <Eye size={14} /> View
          </button>
          {canManage && (
            <>
              <button role="menuitem" onClick={() => runAction(onEdit)}>
                <Pencil size={14} /> Edit
              </button>
              <button role="menuitem" disabled={syncDisabled} onClick={() => runAction(onSync)}>
                <RefreshCw size={14} />
                {syncingId === feed.id ? "Syncing…" : "Sync Now"}
              </button>
            </>
          )}
        </div>,
        document.body,
      )}
    </>
  );
}

export default function FeedList({
  items = [],
  onView,
  onEdit,
  onSync,
  syncingId,
  canManage = false,
}) {
  if (!items.length) {
    return (
      <div className="ti-empty ti-empty--wide">
        No feeds match these filters.
      </div>
    );
  }

  return (
    <div className="ti-feed-table-wrap">
      <table className="ti-feed-table">
        <thead>
          <tr>
            <th scope="col">Feed</th>
            <th scope="col">Type</th>
            <th scope="col">Status</th>
            <th scope="col">Sync Status</th>
            <th scope="col" className="ti-feed-table__number">Indicators</th>
            <th scope="col">Last Sync</th>
            <th scope="col">Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((feed) => {
            const syncDisabled =
              !feed.enabled ||
              feed.feed_type === "internal" ||
              syncingId === feed.id ||
              ["queued", "running"].includes(feed.sync_status);

            return (
              <tr key={feed.id}>
                <td className="ti-feed-table__name">
                  <strong>{feed.name}</strong>
                  {feed.latest_error && (
                    <span className="ti-feed-table__error" title={feed.latest_error}>
                      {feed.latest_error}
                    </span>
                  )}
                </td>
                <td>{displayLabel(feed.feed_type)}</td>
                <td>
                  <span
                    className={`ti-status ti-status--${feed.enabled ? "active" : "inactive"}`}
                  >
                    {feed.enabled ? "Active" : "Inactive"}
                  </span>
                </td>
                <td>
                  <span className={`ti-sync--${feed.sync_status}`}>
                    {displayLabel(feed.sync_status)}
                  </span>
                </td>
                <td className="ti-feed-table__number">
                  {Number(feed.imported_indicator_count).toLocaleString()}
                </td>
                <td>{displayDate(feed.last_sync_at)}</td>
                <td>
                  <div className="ti-feed-table__actions">
                    <FeedActionMenu
                      feed={feed}
                      canManage={canManage}
                      syncDisabled={syncDisabled}
                      syncingId={syncingId}
                      onView={onView}
                      onEdit={onEdit}
                      onSync={onSync}
                    />
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
