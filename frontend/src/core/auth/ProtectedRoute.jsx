import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "./AuthProvider";
import {
  hasAllPermissions,
  hasAnyPermission,
} from "../permissions/permissions";

export default function ProtectedRoute({
  permission,
  permissions = [],
  mode = "all",
}) {
  const {
    accessToken,
    user,
  } = useAuth();

  if (!accessToken) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }

  if (permission) {
    const allowed = hasAnyPermission(user, [permission]);

    if (!allowed) {
      return (
        <Navigate
          to="/unauthorized"
          replace
        />
      );
    }
  }

  if (
    Array.isArray(permissions) &&
    permissions.length > 0
  ) {
    const allowed =
      mode === "any"
        ? hasAnyPermission(
            user,
            permissions,
          )
        : hasAllPermissions(
            user,
            permissions,
          );

    if (!allowed) {
      return (
        <Navigate
          to="/unauthorized"
          replace
        />
      );
    }
  }

  return <Outlet />;
}

export function RoleGuard({ roles, children }) {
  const { user } = useAuth();
  if (!user) return children;
  if (!roles?.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />;
  }
  return children;
}
