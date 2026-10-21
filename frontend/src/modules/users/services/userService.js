import { apiRequest } from "../../../core/api/client";

export async function getUsers(
  token,
  {
    page = 1,
    pageSize = 30,
    search = "",
    role = "",
    isActive,
    isLocked,
  } = {},
) {
  const params = new URLSearchParams();

  params.set("page", String(page));
  params.set("page_size", String(pageSize));

  if (search.trim()) {
    params.set("search", search.trim());
  }

  if (role) {
    params.set("role", role);
  }

  if (typeof isActive === "boolean") {
    params.set("is_active", String(isActive));
  }

  if (typeof isLocked === "boolean") {
    params.set("is_locked", String(isLocked));
  }

  return apiRequest(`/users?${params.toString()}`, {
    method: "GET",
    token,
  });
}

export async function getUser(token, userId) {
  return apiRequest(`/users/${userId}`, {
    method: "GET",
    token,
  });
}

export async function createUser(token, payload) {
  return apiRequest("/users", {
    method: "POST",
    token,
    body: payload,
  });
}

export async function updateUser(
  token,
  userId,
  payload,
) {
  return apiRequest(`/users/${userId}`, {
    method: "PATCH",
    token,
    body: payload,
  });
}

export async function changeUserRole(
  token,
  userId,
  role,
) {
  return apiRequest(`/users/${userId}/role`, {
    method: "PATCH",
    token,
    body: {
      role,
    },
  });
}

export async function enableUser(
  token,
  userId,
) {
  return apiRequest(
    `/users/${userId}/enable`,
    {
      method: "POST",
      token,
    },
  );
}

export async function disableUser(
  token,
  userId,
) {
  return apiRequest(
    `/users/${userId}/disable`,
    {
      method: "POST",
      token,
    },
  );
}
export async function getUserSummary(token) {
  return apiRequest("/users/summary", { method: "GET", token });
}

export async function lockUser(token, userId) {
  return apiRequest(`/users/${userId}/lock`, { method: "POST", token });
}

export async function unlockUser(token, userId) {
  return apiRequest(`/users/${userId}/unlock`, { method: "POST", token });
}

export async function resetUserPassword(token, userId, newPassword) {
  return apiRequest(`/users/${userId}/reset-password`, {
    method: "POST", token, body: { new_password: newPassword },
  });
}

export async function getUserSessions(token, userId) {
  return apiRequest(`/users/${userId}/sessions`, { method: "GET", token });
}

export async function revokeUserSession(token, userId, sessionId) {
  return apiRequest(`/users/${userId}/sessions/${sessionId}`, { method: "DELETE", token });
}

export async function revokeAllUserSessions(token, userId) {
  return apiRequest(`/users/${userId}/sessions`, { method: "DELETE", token });
}

export async function changeUserForcePassword(token, userId, forcePasswordChange) {
  return apiRequest(`/users/${userId}/force-password-change`, {
    method: "PATCH", token, body: { force_password_change: forcePasswordChange },
  });
}
