from __future__ import annotations

from enum import Enum


class Permission(str, Enum):
    """
    Centralized application permissions.

    Permissions describe what an authenticated user is allowed
    to do. Roles determine which permissions are granted.
    """

    # Profile / self-service
    PROFILE_READ = "profile:read"
    PROFILE_PASSWORD_CHANGE = "profile:password_change"
    PROFILE_SESSIONS_READ = "profile:sessions"
    PROFILE_SESSION_REVOKE = "profile:sessions:revoke"

    # User management
    USERS_READ = "users:read"
    USERS_CREATE = "users:create"
    USERS_UPDATE = "users:update"
    USERS_ENABLE = "users:enable"
    USERS_DISABLE = "users:disable"
    USERS_LOCK = "users:lock"
    USERS_UNLOCK = "users:unlock"
    USERS_ROLE_CHANGE = "users:role_change"
    USERS_PASSWORD_RESET = "users:password_reset"
    USERS_FORCE_PASSWORD_CHANGE = "users:force_password_change"

    # Email collection
    EMAILS_READ = "emails:read"
    EMAILS_INGEST = "emails:ingest"

    # Investigation and reporting
    INVESTIGATION_READ = "investigation:read"
    INVESTIGATION_NOTE_CREATE = "investigation:note:create"
    INVESTIGATION_NOTE_UPDATE = "investigation:note:update"
    INVESTIGATION_NOTE_DELETE = "investigation:note:delete"
    INVESTIGATION_AUDIT_READ = "investigation:audit:read"
    EVIDENCE_CREATE = "evidence:create"
    EVIDENCE_READ = "evidence:read"
    EVIDENCE_UPDATE = "evidence:update"
    EVIDENCE_REVIEW = "evidence:review"
    EVIDENCE_EXPORT = "evidence:export"
    EVIDENCE_AUDIT_READ = "evidence:audit:read"
    REPORT_CREATE = "reports:create"
    REPORT_UPDATE = "reports:update"
    REPORT_GENERATE = "reports:generate"
    REPORT_DOWNLOAD = "reports:download"
    REPORT_ARCHIVE = "reports:archive"
    REPORT_AUDIT_READ = "reports:audit:read"

    # System
    SYSTEM_HEALTH_READ = "system:health"

    # Audit, security monitoring and administration
    AUDIT_READ = "audit:read"
    AUDIT_EXPORT = "audit:export"
    SECURITY_EVENTS_READ = "security_events:read"
    SECURITY_ALERTS_READ = "security_alerts:read"
    SECURITY_ALERTS_INVESTIGATE = "security_alerts:investigate"
    MONITORING_RULES_READ = "monitoring_rules:read"
    MONITORING_RULES_MANAGE = "monitoring_rules:manage"
    SYSTEM_SETTINGS_READ = "system_settings:read"
    SYSTEM_SETTINGS_UPDATE = "system_settings:update"
    BACKGROUND_JOBS_READ = "background_jobs:read"
    BACKGROUND_JOBS_MANAGE = "background_jobs:manage"

    # Analytics and experiment tracking
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_EXPORT = "analytics:export"
    EXPERIMENTS_READ = "experiments:read"
    EXPERIMENTS_MANAGE = "experiments:manage"

    # Threat intelligence
    THREAT_INTELLIGENCE_READ = "threat_intelligence:read"
    THREAT_INTELLIGENCE_EXPORT = "threat_intelligence:export"
    THREAT_INDICATORS_MANAGE = "threat_indicators:manage"
    THREAT_FEEDS_MANAGE = "threat_feeds:manage"
    THREAT_MATCHES_INVESTIGATE = "threat_matches:investigate"
