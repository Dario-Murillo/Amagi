import { API_BASE } from "@/lib/config";
import { errorDetail } from "@/lib/errors";
import type { Room, StoredMessage } from "@/lib/types";

/**
 * The room list comes from the database, seeded by migration. It used to be a
 * `FIXED_ROOMS` constant here, which could drift from what the API would
 * actually accept a socket for.
 */
export async function fetchRooms(token: string): Promise<Room[]> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE}/rooms`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch {
    throw new Error("Could not reach the server.");
  }

  const data = await response.json();

  if (!response.ok) {
    throw new Error(errorDetail(data, "Could not load the rooms."));
  }

  return data;
}

/**
 * One page of a room's history, oldest first: the newest page without `before`,
 * the page just older than message `before` with it. Empty means there is
 * nothing older left.
 */
export async function fetchMessages(
  slug: string,
  token: string,
  before?: number,
): Promise<StoredMessage[]> {
  const query = before === undefined ? "" : `?before=${before}`;
  const response = await fetch(`${API_BASE}/rooms/${slug}/messages${query}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await response.json();

  if (!response.ok) {
    throw new Error(errorDetail(data, "Could not load the messages."));
  }

  return data;
}
