# Amagi — Web Client

The Next.js frontend for [Amagi](../README.md). React + TypeScript + Tailwind CSS v4, App Router.

## Running

The package manager is **pnpm**.

```bash
pnpm install
pnpm dev      # http://localhost:3000
pnpm lint
pnpm build
```

The API must be running separately — see the root README for backend setup.

## Configuration

`lib/config.ts` defaults to `http://localhost:8000/api/v1`, so a local run needs no
environment file. To point elsewhere, copy `.env.example` to `.env.local` and set
`NEXT_PUBLIC_API_BASE` and `NEXT_PUBLIC_WS_BASE`. Both values include the `/api/v1`
prefix that every route, including the WebSocket endpoint, is mounted under.

The API matches CORS origins exactly, so the host you open in the browser must be
listed in the backend's `settings.cors_origins`.

## Layout

| Path | Purpose |
| --- | --- |
| `app/page.tsx` | Client Component that switches between splash, auth, rooms, and chat |
| `app/globals.css` | Tailwind import plus the `@theme` design tokens |
| `components/` | The three screens, the splash, and the wordmark |
| `hooks/use-auth.ts` | Session state, login, register, logout |
| `hooks/use-chat-socket.ts` | Room socket lifecycle, messages, and roster |
| `lib/` | Config, fixed rooms, session store, error formatting, shared types |

## Notes for contributors

- **State lives on the client.** There is no server-side data fetching; the session is
  read from `localStorage` through `lib/session-store.ts` via `useSyncExternalStore`,
  which keeps it hydration-safe and in step across tabs.
- **`ChatScreen` must be rendered with `key={room.id}`.** `useChatSocket` never clears
  its messages or roster — a room change resets them by remounting.
- **Lint before pushing.** The React Compiler rules in `eslint-config-next` reject
  patterns that typecheck fine, notably synchronous `setState` inside an effect.
