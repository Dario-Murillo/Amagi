import type { ChatMessage, StoredMessage } from "@/lib/types";

// Pure on purpose: no React, no runtime imports, so it runs under plain Node.

let systemLines = 0;

function formatTime(iso?: string): string {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function byTime(a: ChatMessage, b: ChatMessage) {
  return a.at - b.at || a.id - b.id;
}

/** Adds what is not on screen yet, by key, and keeps the list in time order. */
export function merge(prev: ChatMessage[], incoming: ChatMessage[]): ChatMessage[] {
  const seen = new Set(prev.map((message) => message.key));
  const fresh = incoming.filter((message) => !seen.has(message.key));
  return fresh.length === 0 ? prev : [...prev, ...fresh].sort(byTime);
}

export function fromStored(message: StoredMessage, self: string): ChatMessage {
  return {
    key: `m${message.id}`,
    id: message.id,
    at: Date.parse(message.timestamp),
    author: message.username,
    text: message.message,
    time: formatTime(message.timestamp),
    own: message.username === self,
    system: false,
  };
}

export function systemLine(text: string, at: number): ChatMessage {
  return {
    key: `s${systemLines++}`,
    id: 0,
    at,
    author: "",
    text,
    time: "",
    own: false,
    system: true,
  };
}
