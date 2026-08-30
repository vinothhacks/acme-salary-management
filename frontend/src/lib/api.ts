import type { UiAction } from "./chartRegistry";

const envBase = (import.meta.env.VITE_API_BASE as string | undefined)?.replace(/\/$/, "");
// Production uses same-origin /api (Vercel rewrite) so Safari/iOS keeps the session cookie.
const BASE = import.meta.env.PROD ? "/api" : envBase || "/api";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${BASE}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });
  if (response.status === 401) {
    throw new Error("Unauthorized");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    const detail = body.detail;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  login: (email: string, password: string) =>
    request<{ email: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  logout: () => request<{ status: string }>("/auth/logout", { method: "POST" }),
  me: () => request<{ email: string }>("/auth/me"),
  departments: () => request<{ id: number; name: string }[]>("/departments"),
  employees: (params: URLSearchParams) => request(`/employees?${params.toString()}`),
  employee: (id: number) => request(`/employees/${id}`),
  createEmployee: (body: unknown) =>
    request("/employees", { method: "POST", body: JSON.stringify(body) }),
  patchEmployee: (id: number, body: unknown) =>
    request(`/employees/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  reviseSalary: (id: number, body: unknown) =>
    request(`/employees/${id}/salary-revisions`, { method: "POST", body: JSON.stringify(body) }),
  importCsv: (file: File) => {
    const data = new FormData();
    data.append("file", file);
    return request("/employees/import", { method: "POST", body: data });
  },
  exportUrl: (params: URLSearchParams) => `${BASE}/employees/export?${params.toString()}`,
  summary: () => request("/analytics/summary"),
  distribution: () => request("/analytics/distribution"),
  percentiles: () => request("/analytics/percentiles"),
  costTrend: () => request("/analytics/cost-trend"),
  ask: (message: string, history: { role: "user" | "assistant"; content: string }[]) =>
    request<{ say: string; actions: UiAction[]; model: string | null }>("/ask/chat", {
      method: "POST",
      body: JSON.stringify({ message, history }),
    }),
};
