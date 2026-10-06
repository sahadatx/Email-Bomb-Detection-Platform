const STORAGE_KEY = "email_bomb_auth";

const emptyAuthState = {
  accessToken: null,
  user: null,
};

export function getAuthState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);

    if (!raw) {
      return emptyAuthState;
    }

    const parsed = JSON.parse(raw);

    return {
      accessToken: parsed?.accessToken ?? null,
      user: parsed?.user ?? null,
    };
  } catch {
    return emptyAuthState;
  }
}

export function setAuthState(state) {
  const nextState = {
    accessToken: state?.accessToken ?? null,
    user: state?.user ?? null,
  };

  localStorage.setItem(STORAGE_KEY, JSON.stringify(nextState));

  return nextState;
}

export function clearAuthState() {
  localStorage.removeItem(STORAGE_KEY);
}

export function isAuthenticated() {
  return Boolean(getAuthState().accessToken);
}