const TOKEN_KEY = "milan_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

/** Error de validación (422) con los mensajes agrupados por campo. */
export class ApiValidationError extends ApiError {
  fields: Record<string, string>;

  constructor(status: number, message: string, fields: Record<string, string>) {
    super(status, message);
    this.fields = fields;
  }
}

export async function api<T>(
  path: string,
  options: { method?: string; body?: unknown; formData?: FormData; isForm?: boolean } = {}
): Promise<T> {
  const { method = "GET", body, formData } = options;
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let payload: BodyInit | undefined;
  if (formData) {
    payload = formData;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const res = await fetch(`/api${path}`, { method, headers, body: payload });

  if (res.status === 401) {
    setToken(null);
    window.dispatchEvent(new Event("milan-unauthorized"));
  }

  if (!res.ok) {
    let detail = `Error ${res.status}`;
    let fields: Record<string, string> = {};
    try {
      const data = await res.json();
      if (typeof data.detail === "string") detail = data.detail;
      else if (Array.isArray(data.detail)) {
        const msgs: string[] = [];
        for (const d of data.detail as { loc?: unknown[]; msg?: string }[]) {
          if (d.msg) {
            msgs.push(d.msg);
            const loc = d.loc;
            const key = Array.isArray(loc) && loc.length >= 2 ? String(loc[loc.length - 1]) : null;
            if (key) fields[key] = d.msg;
          }
        }
        detail = msgs.join("; ");
      }
    } catch {
      /* ignore */
    }
    if (Object.keys(fields).length > 0) throw new ApiValidationError(res.status, detail, fields);
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const apiGet = <T>(path: string) => api<T>(path);
export const apiPost = <T>(path: string, body?: unknown) => api<T>(path, { method: "POST", body });
export const apiPatch = <T>(path: string, body?: unknown) => api<T>(path, { method: "PATCH", body });
export const apiDelete = <T>(path: string) => api<T>(path, { method: "DELETE" });