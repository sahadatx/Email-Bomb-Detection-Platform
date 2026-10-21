import { USER_ROLES } from "../types";

const ROLE_LABELS = {
  [USER_ROLES.ADMIN]: "Admin",
  [USER_ROLES.SECURITY_ANALYST]: "Security Analyst",
  [USER_ROLES.EMAIL_ANALYST]: "Email Analyst",
  [USER_ROLES.VIEWER]: "Viewer",
};

export default function RoleSelector({
  value,
  onChange,
  includeAll = true,
}) {
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className="users-filter-select"
    >
      {includeAll && (
        <option value="">
          All roles
        </option>
      )}

      {Object.values(USER_ROLES).map((role) => (
        <option key={role} value={role}>
          {ROLE_LABELS[role]}
        </option>
      ))}
    </select>
  );
}