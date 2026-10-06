export const ROLE_ACCESS = Object.freeze({
  "/ml-models/models": ["ADMIN", "SECURITY_ANALYST", "VIEWER"],
  "/ml-models/training-runs": ["ADMIN", "SECURITY_ANALYST"],
  "/ml-models/registry": ["ADMIN", "SECURITY_ANALYST", "VIEWER"],
  "/ml-models/evaluation": ["ADMIN", "SECURITY_ANALYST", "EMAIL_ANALYST", "VIEWER"],
  "/detection/settings": ["ADMIN"],
  "/detection/new": ["ADMIN", "SECURITY_ANALYST", "EMAIL_ANALYST"],
  "/evidence": ["ADMIN", "SECURITY_ANALYST", "EMAIL_ANALYST"],
  "/experiments": ["ADMIN", "SECURITY_ANALYST"],
  "/audit": ["ADMIN"],
  "/security-monitoring": ["ADMIN", "SECURITY_ANALYST"],
  "/administration": ["ADMIN"],
  "/threat-intelligence/feeds": ["ADMIN", "SECURITY_ANALYST"],
  "/users": ["ADMIN"],
  "/settings": ["ADMIN"],
});
const VALID_ROLES = new Set(["ADMIN", "SECURITY_ANALYST", "EMAIL_ANALYST", "VIEWER"]);

export function canAccessPath(role, path) {
  if (!role) return true;
  if (!VALID_ROLES.has(role)) return false;
  const matchingPath = Object.keys(ROLE_ACCESS)
    .sort((a, b) => b.length - a.length)
    .find((candidate) => path === candidate || path.startsWith(`${candidate}/`));
  return !matchingPath || ROLE_ACCESS[matchingPath].includes(role);
}
