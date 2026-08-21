import type { Session } from "@/lib/types";

const TOKEN_KEY = "amagi_token";
const USER_KEY = "amagi_user";

const listeners = new Set<() => void>();

let cached: Session | null = null;
let cachedKey: string | null = null;

/**
 * `useSyncExternalStore` compares snapshots by identity and re-reads on every
 * render, so an unchanged session has to come back as the very same object or
 * React loops forever.
 */
function read(): Session | null {
  const token = localStorage.getItem(TOKEN_KEY);
  const username = localStorage.getItem(USER_KEY);
  const key = `${token}${username}`;

  if (key !== cachedKey) {
    cachedKey = key;
    cached = token && username ? { token, username } : null;
  }

  return cached;
}

function emit() {
  for (const listener of listeners) listener();
}

export function subscribeSession(listener: () => void) {
  listeners.add(listener);
  // Keeps other tabs of the app in step with a login or logout here.
  window.addEventListener("storage", listener);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", listener);
  };
}

export function getSessionSnapshot(): Session | null {
  return read();
}

/** There is no stored session on the server; the client supplies the real one. */
export function getServerSessionSnapshot(): Session | null {
  return null;
}

export function saveSession(session: Session) {
  localStorage.setItem(TOKEN_KEY, session.token);
  localStorage.setItem(USER_KEY, session.username);
  emit();
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  emit();
}
