import UserStatusBadge from "./UserStatusBadge";

const ROLE_LABELS = {
  ADMIN: "Admin",
  SECURITY_ANALYST: "Security Analyst",
  EMAIL_ANALYST: "Email Analyst",
  VIEWER: "Viewer",
};

function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export default function UserTable({
  users,
  onViewUser,
}) {
  if (!users.length) {
    return (
      <div className="users-empty">
        <div className="users-empty-icon">
          👤
        </div>

        <h3>No users found</h3>

        <p>
          No users match the current filters.
        </p>
      </div>
    );
  }

  return (
    <div className="users-table-wrapper">
      <table className="users-table">
        <thead>
          <tr>
            <th>User</th>
            <th>Role</th>
            <th>Status</th>
            <th>Last Login</th>
            <th>Created</th>
            <th aria-label="Actions" />
          </tr>
        </thead>

        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>
                <div className="user-cell">
                  <div className="user-avatar">
                    {(
                      user.full_name ||
                      user.username ||
                      user.email ||
                      "U"
                    )
                      .charAt(0)
                      .toUpperCase()}
                  </div>

                  <div className="user-identity">
                    <strong>
                      {user.full_name || "Unnamed User"}
                    </strong>

                    <span>
                      {user.email}
                    </span>

                    <small>
                      @{user.username}
                    </small>
                  </div>
                </div>
              </td>

              <td>
                <span className="user-role-badge">
                  {ROLE_LABELS[user.role] || user.role}
                </span>
              </td>

              <td>
                <UserStatusBadge user={user} />
              </td>

              <td>
                {formatDate(user.last_login_at)}
              </td>

              <td>
                {formatDate(user.created_at)}
              </td>

              <td>
                <button
                  type="button"
                  className="table-action-button"
                  onClick={() => onViewUser(user)}
                >
                  View
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}