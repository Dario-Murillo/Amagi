import { API_BASE } from "@/lib/config";
import { errorDetail } from "@/lib/errors";
import { clearSession, getSessionSnapshot } from "@/lib/session-store";
import type { Room, StoredMessage } from "@/lib/types";

/**
 * GET with the session's token. A 401 means the token expired or was revoked by
 * a logout on another device, and no retry can fix that, so the stored session
 * is dropped and every screen falls back to the sign-in form.
 */
async function authedGet<T>(path: string, token: string, fallback: string): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch {
    throw new Error("Could not reach the server.");
  }

  if (response.status === 401) {
    // Only if it is still the stored token: a request that set off before a
    // fresh login in another tab must not sign that new session out.
    if (getSessionSnapshot()?.token === token) clearSession();
    throw new Error("Your session has expired.");
  }

  const data = await response.json();

  if (!response.ok) {
    throw new Error(errorDetail(data, fallback));
  }

  return data;
}

/**
 * The room list comes from the database, seeded by migration. It used to be a
 * `FIXED_ROOMS` constant here, which could drift from what the API would
 * actually accept a socket for.
 */
export function fetchRooms(token: string): Promise<Room[]> {
  return authedGet("/rooms", token, "Could not load the rooms.");
}

/**
 * One page of a room's history, oldest first: the newest page without `before`,
 * the page just older than message `before` with it. Empty means there is
 * nothing older left.
 */
export function fetchMessages(
  slug: string,
  token: string,
  before?: number,
): Promise<StoredMessage[]> {
  const query = before === undefined ? "" : `?before=${before}`;
  return authedGet(
    `/rooms/${slug}/messages${query}`,
    token,
    "Could not load the messages.",
  );
}
