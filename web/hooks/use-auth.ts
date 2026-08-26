"use client";

import { useCallback, useState, useSyncExternalStore } from "react";
import { API_BASE } from "@/lib/config";
import { errorDetail } from "@/lib/errors";
import {
  clearSession,
  getServerSessionSnapshot,
  getSessionSnapshot,
  saveSession,
  subscribeSession,
} from "@/lib/session-store";
import type { Session } from "@/lib/types";

// Hydration probe: false while rendering on the server and during hydration,
// true from the first client render onward. Lets the caller hold the first
// paint instead of flashing the auth screen at a signed-in user.
const noopSubscribe = () => () => {};
const alwaysTrue = () => true;
const alwaysFalse = () => false;

export function useAuth() {
  const session = useSyncExternalStore(
    subscribeSession,
    getSessionSnapshot,
    getServerSessionSnapshot,
  );
  const ready = useSyncExternalStore(noopSubscribe, alwaysTrue, alwaysFalse);

  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const clearError = useCallback(() => setError(""), []);

  const login = useCallback(async (username: string, password: string) => {
    if (!username || !password) {
      setError("Please fill in all fields.");
      return false;
    }

    setIsLoading(true);
    setError("");

    try {
      // OAuth2PasswordRequestForm expects form-encoded data.
      const form = new URLSearchParams({ username, password });

      const res = await fetch(`${API_BASE}/users/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form,
      });

      const data = await res.json();

      if (!res.ok) {
        setError(errorDetail(data, "Login failed."));
        return false;
      }

      // Stored exactly as typed. The server looks usernames up case-sensitively,
      // so a login that succeeded proves this matches the stored account;
      // lower-casing it here made the local copy disagree with the name the
      // server broadcasts, and every message came back looking like a stranger's.
      const next: Session = {
        token: data.access_token,
        username,
      };

      saveSession(next);
      return true;
    } catch {
      setError("Could not reach the server.");
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(
    async (username: string, password: string) => {
      if (!username || !password) {
        setError("Please fill in all fields.");
        return false;
      }

      if (password.length < 8) {
        setError("Password must be at least 8 characters.");
        return false;
      }

      setIsLoading(true);
      setError("");

      try {
        const res = await fetch(`${API_BASE}/users/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        });

        const data = await res.json();

        if (!res.ok) {
          setError(errorDetail(data, "Registration failed."));
          return false;
        }
      } catch {
        setError("Could not reach the server.");
        return false;
      } finally {
        setIsLoading(false);
      }

      // Registration only creates the user; the token comes from /users/token.
      return login(username, password);
    },
    [login],
  );

  const logout = useCallback(() => {
    clearSession();
    setError("");
  }, []);

  return {
    session,
    ready,
    error,
    isLoading,
    login,
    register,
    logout,
    clearError,
  };
}
