// Run with `node lib/messages.check.mjs` (Node 22.18+ strips the types itself).
// Guards the "no message shows twice" rule, which lives only in `merge`.
import assert from "node:assert/strict";
import { fromStored, merge, systemLine } from "./messages.ts";

const stored = (id, second) => ({
  id,
  username: "ghost_99",
  message: `m${id}`,
  timestamp: `2026-09-23T10:00:${String(second).padStart(2, "0")}Z`,
});

// The same row as a live frame and again in a history page: shown once.
let list = merge([], [fromStored(stored(7, 7), "ghost_99")]);
list = merge(list, [5, 6, 7].map((id) => fromStored(stored(id, id), "ghost_99")));
assert.deepEqual(list.map((m) => m.id), [5, 6, 7]);

// An older page lands above, in order, with nothing repeated.
list = merge(list, [3, 4, 5].map((id) => fromStored(stored(id, id), "ghost_99")));
assert.deepEqual(list.map((m) => m.id), [3, 4, 5, 6, 7]);

// A join line keeps its place in time even when history arrives after it.
const joined = systemLine("kira joined the room.", Date.parse("2026-09-23T10:00:08Z"));
list = merge(merge([], [joined]), list);
assert.equal(list.at(-1).key, joined.key);

// Nothing new keeps the same array, so React skips the re-render.
assert.equal(merge(list, [fromStored(stored(4, 4), "ghost_99")]), list);

console.log("messages: ok");
