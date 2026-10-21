import { apiRequest } from "../../../core/api/client";

export async function login(credentials) {
  return apiRequest("/auth/login", {
    method: "POST",
    body: credentials,
  });
}

export async function getCurrentUser(token) {
  return apiRequest("/auth/me", {
    method: "GET",
    token,
  });
}

export async function logout(token) {
  return apiRequest("/auth/logout", {
    method: "POST",
    token,
  });
}