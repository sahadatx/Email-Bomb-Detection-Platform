import axios from "axios";

import { getAuthState } from "../../../core/auth/authState";

const API_BASE_URL = "/api/v1";

function createAuthenticatedApi(baseURL) {
  const client = axios.create({
    baseURL,
    withCredentials: true,
    headers: {
      "Content-Type": "application/json",
    },
  });

  client.interceptors.request.use((config) => {
    const token = getAuthState()?.accessToken;

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  });

  return client;
}

export const mlModelsApi = createAuthenticatedApi(
  `${API_BASE_URL}/ml-models`
);

export const preprocessingApi = createAuthenticatedApi(
  `${API_BASE_URL}/preprocessing`
);
