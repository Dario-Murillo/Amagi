export type Session = {
  token: string;
  username: string;
};

/** Mirrors RoomResponse from the API. `slug` is what addresses a room. */
export type Room = {
  id: number;
  slug: string;
  name: string;
  topic: string;
  description: string;
};

export type ChatMessage = {
  /** `m<id>` for a stored message, `s<n>` for a system line. Two copies of the
   * same row — one from a history page, one live — share a key, which is what
   * keeps a message from showing twice. */
  key: string;
  /** The stored id, or 0 for a system line. */
  id: number;
  /** Epoch ms. The list is ordered by it so history and live frames interleave. */
  at: number;
  author: string;
  text: string;
  /** Already formatted for display, or "" for system lines. */
  time: string;
  own: boolean;
  system: boolean;
};

/** Mirrors MessageResponse from the API, and the fields of a `message` frame. */
export type StoredMessage = {
  id: number;
  username: string;
  message: string;
  timestamp: string;
};

export type WsStatus = "connecting" | "connected" | "disconnected";

export type AuthMode = "login" | "register";

/** Shape of the JSON frames the API broadcasts over a room socket. */
export type ServerFrame = {
  type?: "join" | "message";
  event?: "disconnect";
  id?: number;
  username?: string;
  message?: string;
  room_slug?: string;
  timestamp?: string;
};

export type RoomsState =
  | { status: "loading" }
  | { status: "ready"; rooms: Room[] }
  | { status: "error"; error: string };
