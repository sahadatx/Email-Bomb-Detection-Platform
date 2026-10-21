import { Eye, Pencil, Power } from "lucide-react";
import ActionMenu from "../../investigation-reporting/components/common/ActionMenu";
import { displayLabel } from "../types/threatIntelligence";
export default function IndicatorTable({
  items = [],
  onView,
  onEdit,
  onToggle,
  canManage = false,
}) {
  return (
    <div className="ti-table-wrap">
      <table className="ti-table">
        <thead>
          <tr>
            <th>Indicator</th>
            <th>Type</th>
            <th>Severity</th>
            <th>Status</th>
            <th>Source</th>
            <th>Matches</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((row) => (
            <tr key={row.id} onDoubleClick={() => onView(row)}>
              <td className="ti-indicator-value">{row.value}</td>
              <td>{displayLabel(row.indicator_type)}</td>
              <td>
                <span className={`ti-severity ti-severity--${row.severity}`}>
                  {displayLabel(row.severity)}
                </span>
              </td>
              <td>
                <span className={`ti-status ti-status--${row.status}`}>
                  {displayLabel(row.status)}
                </span>
              </td>
              <td>{row.feed_name || displayLabel(row.source)}</td>
              <td>{row.matches_count}</td>
              <td>
                <div className="ti-row-actions">
                  <ActionMenu
                    label={`Actions for ${row.value}`}
                    className="ti-action-popover"
                    items={[
                      { label: "View details", icon: Eye, onClick: () => onView(row) },
                      ...(canManage
                        ? [
                            { label: "Edit indicator", icon: Pencil, onClick: () => onEdit(row) },
                            {
                              label: row.status === "active" ? "Disable indicator" : "Enable indicator",
                              icon: Power,
                              onClick: () => onToggle(row),
                            },
                          ]
                        : []),
                    ]}
                  />
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!items.length && (
        <div className="ti-empty">No indicators match these filters.</div>
      )}
    </div>
  );
}
