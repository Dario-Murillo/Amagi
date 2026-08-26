"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { WS_BASE } from "@/lib/config";
import type { ChatMessage, ServerFrame, Session, WsStatus } from "@/lib/types";

// Mirrors WS_ROOM_NOT_FOUND in the API: the slug reached no room. The server
// has to accept the socket before sending it, because a code sent while the
// handshake is still open never reaches the browser -- it arrives as a plain
// failed connection. A rejected token is exactly that case, so it cannot be
// told apart here and falls through to the generic message below.
const WS_ROOM_NOT_FOUND = 4004;

// The token rides in `Sec-WebSocket-Protocol` rather than in the query string,
// which is the only header a browser can influence on a WebSocket handshake.
// A token in the URL ends up in the server's access log and in every proxy in
// front of it. Must match WS_BEARER_SUBPROTOCOL in the API.
const WS_BEARER_SUBPROTOCOL = "bearer";

function formatTime(iso?: string): string {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

/**
 * Owns the room socket for as long as the caller is mounted.
 *
 * Messages and members accumulate for the life of the component and are never
 * cleared, so the caller must remount on room change — render it with
 * `key={room.slug}` — rather than swapping the `roomSlug` argument under it.
 */
export function useChatSocket(roomSlug: string, session: Session) {
  const { token, username } = session;

  const [status, setStatus] = useState<WsStatus>("connecting");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [members, setMembers] = useState<string[]>([]);

  const socketRef = useRef<WebSocket | null>(null);
  const nextId = useRef(0);

  useEffect(() => {
    // Set while tearing down so an intentional close does not announce itself
    // as a dropped connection — including StrictMode's double-mount in dev.
    let disposed = false;

    const append = (message: Omit<ChatMessage, "id">) =>
      setMessages((prev) => [...prev, { ...message, id: nextId.current++ }]);

    const appendSystem = (text: string) =>
      append({ author: "", text, time: "", own: false, system: true });

    const socket = new WebSocket(`${WS_BASE}/ws/${roomSlug}`, [
      WS_BEARER_SUBPROTOCOL,
      token,
    ]);
    socketRef.current = socket;

    socket.onopen = () => {
      setStatus("connected");
      socket.send(JSON.stringify({ type: "join", username }));
    };

    socket.onmessage = (event) => {
      let frame: ServerFrame;
      try {
        frame = JSON.parse(event.data as string);
      } catch {
        // Defensive: every frame the server sends is JSON, but this parses
        // input from the network and must not throw inside an event handler.
        return;
      }

      if (frame.event === "disconnect") {
        const who = frame.username ?? "Someone";
        setMembers((prev) => prev.filter((member) => member !== who));
        appendSystem(`${who} left the room.`);
        return;
      }

      if (frame.type === "join") {
        const who = frame.username ?? "Someone";
        setMembers((prev) => (prev.includes(who) ? prev : [...prev, who]));
        appendSystem(`${who} joined the room.`);
        return;
      }

      // Own messages are already on screen from the optimistic render.
      if (frame.username === username) return;

      append({
        author: frame.username ?? "Someone",
        text: frame.message ?? "",
        time: formatTime(frame.timestamp),
        own: false,
        system: false,
      });
    };

    socket.onclose = (event) => {
      if (disposed) return;
      setStatus("disconnected");
      appendSystem(
        event.code === WS_ROOM_NOT_FOUND
          ? "That room does not exist on the server."
          : "Disconnected from room.",
      );
    };

    socket.onerror = () => {
      if (disposed) return;
      setStatus("disconnected");
      appendSystem("Connection error. Is the server running?");
    };

    return () => {
      disposed = true;
      socketRef.current = null;
      socket.close();
    };
  }, [roomSlug, token, username]);

  const send = useCallback(
    (text: string) => {
      const socket = socketRef.current;
      if (!socket || socket.readyState !== WebSocket.OPEN) return false;

      const timestamp = new Date().toISOString();

      socket.send(
        JSON.stringify({
          type: "message",
          username,
          message: text,
          timestamp,
        }),
      );

      setMessages((prev) => [
        ...prev,
        {
          id: nextId.current++,
          author: username,
          text,
          time: formatTime(timestamp),
          own: true,
          system: false,
        },
      ]);

      return true;
    },
    // `send` no longer names the room: the server routes on the socket's own
    // path, so there was nothing left for it to read here.
    [username],
  );

  return { status, messages, members, send };
}
