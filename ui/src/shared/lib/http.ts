const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export class HttpError extends Error {
  readonly status: number;
  readonly code: string | null;
  readonly retryAfterSeconds: number | null;

  constructor(status: number, code: string | null, message: string, retryAfterSeconds: number | null) {
    super(message);
    this.name = "HttpError";
    this.status = status;
    this.code = code;
    this.retryAfterSeconds = retryAfterSeconds;
  }
}

function toHttpError(status: number, body: unknown): HttpError {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (detail && typeof detail === "object" && !Array.isArray(detail)) {
    const d = detail as { code?: string; message?: string; retry_after_seconds?: number };
    return new HttpError(status, d.code ?? null, d.message ?? JSON.stringify(body), d.retry_after_seconds ?? null);
  }
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string };
    return new HttpError(status, null, first.msg ?? JSON.stringify(body), null);
  }
  return new HttpError(status, null, `HTTP ${status}: ${JSON.stringify(body)}`, null);
}

export async function httpJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    throw toHttpError(response.status, await response.json().catch(() => null));
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}
