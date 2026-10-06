import { useAuth } from "../auth/AuthProvider";
import {
  hasAllPermissions,
  hasAnyPermission,
  hasPermission,
} from "./permissions";

export default function Can({
  permission,
  permissions = [],
  mode = "all",
  fallback = null,
  children,
}) {
  const { user } = useAuth();

  let allowed = false;

  if (permission) {
    allowed = hasPermission(
      user,
      permission,
    );
  } else if (
    Array.isArray(permissions) &&
    permissions.length > 0
  ) {
    allowed =
      mode === "any"
        ? hasAnyPermission(
            user,
            permissions,
          )
        : hasAllPermissions(
            user,
            permissions,
          );
  }

  if (!allowed) {
    return fallback;
  }

  return children;
}