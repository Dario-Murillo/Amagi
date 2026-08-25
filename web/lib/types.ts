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
  id: number;
  author: string;
  text: string;
  /** Already formatted for display, or "" for system lines. */
  time: string;
  own: boolean;
  system: boolean;
};

export type WsStatus = "connecting" | "connected" | "disconnected";

export type AuthMode = "login" | "register";

/** Shape of the JSON frames the API broadcasts over a room socket. */
export type ServerFrame = {
  type?: "join" | "message";
  event?: "disconnect";
  username?: string;
  message?: string;
  room_id?: string;
  timestamp?: string;
  client_id?: string;
};
