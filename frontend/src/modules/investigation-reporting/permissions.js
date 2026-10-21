const MANAGE_ROLES = new Set(["ADMIN", "SECURITY_ANALYST"]);

export function getInvestigationAccess(user) {
  const rawRole = user?.role?.value ?? user?.role?.name ?? user?.role ?? "";
  const role = String(rawRole).toUpperCase();
  return {
    role,
    canRead: Boolean(user),
    canManage: MANAGE_ROLES.has(role),
    canEditReports: role === "ADMIN",
    canArchiveReports: role === "ADMIN",
    canReadAudit: role === "ADMIN",
    isAdmin: role === "ADMIN",
    canDownloadReports: Boolean(user),
    canExportEvidence: role === "ADMIN" || role === "SECURITY_ANALYST",
    canReadEvidence: role === "ADMIN" || role === "SECURITY_ANALYST" || role === "EMAIL_ANALYST",
  };
}

export function permissionMessage(action) {
  return `Your account does not have permission to ${action}. Contact an administrator for access.`;
}
