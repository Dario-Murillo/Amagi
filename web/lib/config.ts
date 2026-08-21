/**
 * Both bases already include the `/api/v1` prefix every route is mounted under,
 * including the WebSocket endpoint.
 */
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1";

export const WS_BASE =
  process.env.NEXT_PUBLIC_WS_BASE ?? "ws://localhost:8000/api/v1";
