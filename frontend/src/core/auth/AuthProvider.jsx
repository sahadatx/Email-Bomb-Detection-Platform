import { createContext, useContext, useEffect, useMemo, useState } from "react";

import {
  clearAuthState,
  getAuthState,
  setAuthState,
} from "./authState";
import { apiRequest } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const initialState = getAuthState();

  const [accessToken, setAccessToken] = useState(
    initialState.accessToken,
  );

  const [user, setUser] = useState(initialState.user);

  useEffect(() => {
    if (!accessToken || user) return undefined;
    let active = true;
    apiRequest("/auth/me", { token: accessToken })
      .then((currentUser) => {
        if (!active) return;
        setAuthState({ accessToken, user: currentUser });
        setUser(currentUser);
      })
      .catch(() => {
        // Keep the current session state; protected requests will surface
        // authentication failures through the normal API error handling.
      });
    return () => { active = false; };
  }, [accessToken, user]);

  function login({ accessToken: token, user: authenticatedUser }) {
    const nextState = setAuthState({
      accessToken: token,
      user: authenticatedUser,
    });

    setAccessToken(nextState.accessToken);
    setUser(nextState.user);
  }

  function logout() {
    clearAuthState();

    setAccessToken(null);
    setUser(null);
  }

  const value = useMemo(
    () => ({
      accessToken,
      user,
      isAuthenticated: Boolean(accessToken),
      login,
      logout,
    }),
    [accessToken, user],
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside an AuthProvider.",
    );
  }

  return context;
}
