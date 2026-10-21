export const USER_ROLES = Object.freeze({
  ADMIN: "ADMIN",
  SECURITY_ANALYST: "SECURITY_ANALYST",
  EMAIL_ANALYST: "EMAIL_ANALYST",
  VIEWER: "VIEWER",
});

export const USER_STATUS = Object.freeze({
  ACTIVE: "active",
  DISABLED: "disabled",
  LOCKED: "locked",
});

export const ROLE_LABELS = Object.freeze({
  [USER_ROLES.ADMIN]: "Admin",
  [USER_ROLES.SECURITY_ANALYST]: "Security Analyst",
  [USER_ROLES.EMAIL_ANALYST]: "Email Analyst",
  [USER_ROLES.VIEWER]: "Viewer",
});

export const EMPTY_USER_FORM = Object.freeze({
  email: "",
  username: "",
  full_name: "",
  password: "",
  role: USER_ROLES.VIEWER,
});

export function getUserStatus(user) {
  if (user?.is_locked) {
    return USER_STATUS.LOCKED;
  }

  if (!user?.is_active) {
    return USER_STATUS.DISABLED;
  }

  return USER_STATUS.ACTIVE;
}

export function getRoleLabel(role) {
  return ROLE_LABELS[role] || role || "Unknown";
}