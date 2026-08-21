/**
 * FastAPI reports failures under `detail`, which is a string for HTTPException
 * but a list of validation objects for 422s. Flatten either into one line so it
 * can be rendered directly.
 */
export function errorDetail(body: unknown, fallback: string): string {
  if (typeof body !== "object" || body === null || !("detail" in body)) {
    return fallback;
  }

  const detail = (body as { detail: unknown }).detail;

  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) =>
        typeof item === "object" && item !== null && "msg" in item
          ? String((item as { msg: unknown }).msg)
          : null,
      )
      .filter((msg): msg is string => msg !== null);

    if (messages.length > 0) return messages.join(" · ");
  }

  return fallback;
}
