import { getUserStatus } from "../types";

const STATUS_CONFIG = {
  active: {
    label: "Active",
    className: "user-status-badge user-status-active",
  },
  disabled: {
    label: "Disabled",
    className: "user-status-badge user-status-disabled",
  },
  locked: {
    label: "Locked",
    className: "user-status-badge user-status-locked",
  },
};

export default function UserStatusBadge({ user }) {
  const status = getUserStatus(user);
  const config = STATUS_CONFIG[status];

  return (
    <span className={config.className}>
      <span className="user-status-dot" />
      {config.label}
    </span>
  );
}