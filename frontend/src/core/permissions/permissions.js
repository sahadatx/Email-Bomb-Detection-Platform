export const PERMISSIONS = Object.freeze({
  PROFILE_READ: "profile:read",
  PROFILE_PASSWORD_CHANGE:
    "profile:password_change",
  PROFILE_SESSIONS_READ:
    "profile:sessions",
  PROFILE_SESSION_REVOKE:
    "profile:sessions:revoke",

  USERS_READ: "users:read",
  USERS_CREATE: "users:create",
  USERS_UPDATE: "users:update",
  USERS_ENABLE: "users:enable",
  USERS_DISABLE: "users:disable",
  USERS_LOCK: "users:lock",
  USERS_UNLOCK: "users:unlock",
  USERS_ROLE_CHANGE:
    "users:role_change",
  USERS_PASSWORD_RESET:
    "users:password_reset",
  USERS_FORCE_PASSWORD_CHANGE:
    "users:force_password_change",

  EMAILS_READ: "emails:read",
  EMAILS_INGEST: "emails:ingest",
  INVESTIGATION_READ: "investigation:read",
  INVESTIGATION_NOTE_CREATE: "investigation:note:create",
  INVESTIGATION_NOTE_UPDATE: "investigation:note:update",
  INVESTIGATION_NOTE_DELETE: "investigation:note:delete",
  EVIDENCE_READ: "evidence:read",
  EVIDENCE_CREATE: "evidence:create",
  EVIDENCE_UPDATE: "evidence:update",
  EVIDENCE_REVIEW: "evidence:review",
  EVIDENCE_EXPORT: "evidence:export",
  REPORT_CREATE: "reports:create",
  REPORT_UPDATE: "reports:update",
  REPORT_GENERATE: "reports:generate",
  REPORT_DOWNLOAD: "reports:download",
  AUDIT_READ: "audit:read",
  SECURITY_EVENTS_READ: "security_events:read",
  SECURITY_ALERTS_READ: "security_alerts:read",
  SECURITY_ALERTS_INVESTIGATE: "security_alerts:investigate",
  MONITORING_RULES_READ: "monitoring_rules:read",
  MONITORING_RULES_MANAGE: "monitoring_rules:manage",
  ANALYTICS_READ: "analytics:read",
  ANALYTICS_EXPORT: "analytics:export",
  EXPERIMENTS_READ: "experiments:read",
  EXPERIMENTS_MANAGE: "experiments:manage",
  THREAT_INTELLIGENCE_READ: "threat_intelligence:read",
  THREAT_INTELLIGENCE_EXPORT: "threat_intelligence:export",
  THREAT_INDICATORS_MANAGE: "threat_indicators:manage",
  THREAT_FEEDS_MANAGE: "threat_feeds:manage",
  THREAT_MATCHES_INVESTIGATE: "threat_matches:investigate",

  SYSTEM_HEALTH_READ:
    "system:health",
  SYSTEM_SETTINGS_READ: "system_settings:read",
  SYSTEM_SETTINGS_UPDATE: "system_settings:update",
});

const PROFILE_PERMISSIONS = [
  PERMISSIONS.PROFILE_READ,
  PERMISSIONS.PROFILE_PASSWORD_CHANGE,
  PERMISSIONS.PROFILE_SESSIONS_READ,
  PERMISSIONS.PROFILE_SESSION_REVOKE,
];

const SECURITY_ANALYST_PERMISSIONS = [
  ...PROFILE_PERMISSIONS,
  PERMISSIONS.EMAILS_READ, PERMISSIONS.EMAILS_INGEST,
  PERMISSIONS.INVESTIGATION_READ,
  PERMISSIONS.INVESTIGATION_NOTE_CREATE,
  PERMISSIONS.INVESTIGATION_NOTE_UPDATE,
  PERMISSIONS.INVESTIGATION_NOTE_DELETE,
  PERMISSIONS.EVIDENCE_READ, PERMISSIONS.EVIDENCE_CREATE,
  PERMISSIONS.EVIDENCE_UPDATE, PERMISSIONS.EVIDENCE_REVIEW,
  PERMISSIONS.EVIDENCE_EXPORT, PERMISSIONS.REPORT_CREATE,
  PERMISSIONS.REPORT_GENERATE, PERMISSIONS.REPORT_DOWNLOAD,
  PERMISSIONS.SECURITY_EVENTS_READ, PERMISSIONS.SECURITY_ALERTS_READ,
  PERMISSIONS.MONITORING_RULES_READ, PERMISSIONS.ANALYTICS_READ,
  PERMISSIONS.ANALYTICS_EXPORT, PERMISSIONS.EXPERIMENTS_READ,
  PERMISSIONS.EXPERIMENTS_MANAGE, PERMISSIONS.THREAT_INTELLIGENCE_READ,
  PERMISSIONS.THREAT_INTELLIGENCE_EXPORT,
  PERMISSIONS.THREAT_INDICATORS_MANAGE, PERMISSIONS.THREAT_FEEDS_MANAGE,
  PERMISSIONS.THREAT_MATCHES_INVESTIGATE,
];

const READ_ONLY_PERMISSIONS = [
  ...PROFILE_PERMISSIONS,
  PERMISSIONS.EMAILS_READ,
  PERMISSIONS.EMAILS_READ,
  PERMISSIONS.INVESTIGATION_READ,
  PERMISSIONS.REPORT_DOWNLOAD,
  PERMISSIONS.ANALYTICS_READ,
  PERMISSIONS.THREAT_INTELLIGENCE_READ,
];

const ROLE_PERMISSIONS = {
  ADMIN: Object.values(PERMISSIONS),
  SECURITY_ANALYST: SECURITY_ANALYST_PERMISSIONS,
  EMAIL_ANALYST: [
    ...PROFILE_PERMISSIONS, PERMISSIONS.EMAILS_READ, PERMISSIONS.EMAILS_INGEST,
    PERMISSIONS.INVESTIGATION_READ, PERMISSIONS.REPORT_DOWNLOAD,
    PERMISSIONS.EVIDENCE_READ,
    PERMISSIONS.ANALYTICS_READ, PERMISSIONS.THREAT_INTELLIGENCE_READ,
  ],
  VIEWER: READ_ONLY_PERMISSIONS,
};

export function hasPermission(
  user,
  permission,
) {
  if (!user || !permission) {
    return false;
  }

  if (Array.isArray(user.permissions)) return user.permissions.includes(permission);
  return ROLE_PERMISSIONS[user.role]?.includes(permission) ?? false;
}

export function hasAnyPermission(
  user,
  permissions,
) {
  if (!user || !Array.isArray(permissions)) {
    return false;
  }

  return permissions.some(
    (permission) =>
      hasPermission(
        user,
        permission,
      ),
  );
}

export function hasAllPermissions(
  user,
  permissions,
) {
  if (!user || !Array.isArray(permissions)) {
    return false;
  }

  return permissions.every(
    (permission) =>
      hasPermission(
        user,
        permission,
      ),
  );
}
