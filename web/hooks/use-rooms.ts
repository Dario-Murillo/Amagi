"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchRooms } from "@/lib/rooms";
import type { Room } from "@/lib/types";

type RoomsState =
  | { status: "loading" }
  | { status: "ready"; rooms: Room[] }
  | { status: "error"; error: string };

/**
 * Loads the room list for the session. This is the app's only data fetch, so it
 * carries the loading and error states the room screen renders.
 *
 * The three outcomes live in one state value rather than three: it keeps the
 * effect from writing state synchronously — which the React Compiler rules
 * reject — and makes an impossible pair like "loading with an error" unspellable.
 */
export function useRooms(token: string) {
  const [state, setState] = useState<RoomsState>({ status: "loading" });
  // Bumped by `retry` to re-run the effect without touching the token.
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    // A settled fetch must not write state after the screen is gone.
    let cancelled = false;

    fetchRooms(token)
      .then((rooms) => {
        if (!cancelled) setState({ status: "ready", rooms });
      })
      .catch((cause: unknown) => {
        if (cancelled) return;
        setState({
          status: "error",
          error:
            cause instanceof Error ? cause.message : "Could not load the rooms.",
        });
      });

    return () => {
      cancelled = true;
    };
  }, [token, attempt]);

  const retry = useCallback(() => {
    // Safe here, unlike inside the effect: this runs from a click.
    setState({ status: "loading" });
    setAttempt((value) => value + 1);
  }, []);

  return {
    rooms: state.status === "ready" ? state.rooms : [],
    error: state.status === "error" ? state.error : "",
    isLoading: state.status === "loading",
    retry,
  };
}
