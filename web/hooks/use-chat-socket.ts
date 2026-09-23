"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { WS_BASE } from "@/lib/config";
import { fromStored, merge, systemLine } from "@/lib/messages";
import { fetchMessages } from "@/lib/rooms";
import type {
  ChatMessage,
  ServerFrame,
  Session,
  StoredMessage,
  WsStatus,
} from "@/lib/types";

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

/**
 * Owns the room socket and its history for as long as the caller is mounted.
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
  const loadingOlder = useRef(false);
  // Set once a history page comes back empty: the start of the room.
  const reachedStart = useRef(false);

  useEffect(() => {
    // Set while tearing down so an intentional close does not announce itself
    // as a dropped connection — including StrictMode's double-mount in dev.
    let disposed = false;

    const add = (incoming: ChatMessage[]) =>
      setMessages((prev) => merge(prev, incoming));

    const socket = new WebSocket(`${WS_BASE}/ws/${roomSlug}`, [
      WS_BEARER_SUBPROTOCOL,
      token,
    ]);
    socketRef.current = socket;

    socket.onopen = () => {
      setStatus("connected");
      socket.send(JSON.stringify({ type: "join" }));

      // Only once the socket is open, so nothing sent in between can be missed:
      // a message is either stored before this query runs or broadcast to us
      // after it. One that is both is dropped by key in `merge`.
      fetchMessages(roomSlug, token)
        .then((page) => {
          if (disposed) return;
          if (page.length === 0) reachedStart.current = true;
          add(page.map((message) => fromStored(message, username)));
        })
        .catch(() => {
          if (!disposed) add([systemLine("Could not load earlier messages.", Date.now())]);
        });
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

      const at = frame.timestamp ? Date.parse(frame.timestamp) : Date.now();

      if (frame.event === "disconnect") {
        const who = frame.username ?? "Someone";
        setMembers((prev) => prev.filter((member) => member !== who));
        add([systemLine(`${who} left the room.`, at)]);
        return;
      }

      if (frame.type === "join") {
        const who = frame.username ?? "Someone";
        setMembers((prev) => (prev.includes(who) ? prev : [...prev, who]));
        add([systemLine(`${who} joined the room.`, at)]);
        return;
      }

      // Rendered only from the server's copy, own messages included: no
      // optimistic line to reconcile, and a second tab of the same account sees
      // them too.
      if (frame.id !== undefined) {
        add([fromStored(frame as StoredMessage, username)]);
      }
    };

    socket.onclose = (event) => {
      if (disposed) return;
      setStatus("disconnected");
      add([
        systemLine(
          event.code === WS_ROOM_NOT_FOUND
            ? "That room does not exist on the server."
            : "Disconnected from room.",
          Date.now(),
        ),
      ]);
    };

    socket.onerror = () => {
      if (disposed) return;
      setStatus("disconnected");
      add([systemLine("Connection error. Is the server running?", Date.now())]);
    };

    return () => {
      disposed = true;
      socketRef.current = null;
      socket.close();
    };
  }, [roomSlug, token, username]);

  // Keyset cursor: the smallest stored id on screen, not the first in time
  // order — history pages are cut by id.
  const oldestId = messages.reduce<number | undefined>(
    (min, message) =>
      message.system || (min !== undefined && min <= message.id) ? min : message.id,
    undefined,
  );

  const loadOlder = useCallback(async () => {
    if (loadingOlder.current || reachedStart.current || oldestId === undefined) {
      return;
    }

    loadingOlder.current = true;
    try {
      const page = await fetchMessages(roomSlug, token, oldestId);
      if (page.length === 0) reachedStart.current = true;
      setMessages((prev) =>
        merge(prev, page.map((message) => fromStored(message, username))),
      );
    } catch {
      // Left retryable: the next scroll to the top asks again.
    } finally {
      loadingOlder.current = false;
    }
  }, [oldestId, roomSlug, token, username]);

  const send = useCallback((text: string) => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) return false;

    socket.send(JSON.stringify({ type: "message", message: text }));
    return true;
  }, []);

  return { status, messages, members, send, loadOlder };
}
