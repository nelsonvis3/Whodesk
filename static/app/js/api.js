// Cliente HTTP: mismo origen, sesión por cookie y CSRF por cabecera.
export class ApiError extends Error {
  constructor(status, data) {
    super(messageOf(data, status));
    this.status = status;
    this.data = data;
  }
}

function messageOf(data, status) {
  if (!data) return status === 429 ? "Demasiadas solicitudes. Esperá un momento." : "Error de conexión con el servidor.";
  if (typeof data === "string") return data;
  if (data.detail) return String(data.detail);
  const parts = [];
  for (const [field, val] of Object.entries(data)) {
    const text = Array.isArray(val) ? val.join(" ") : typeof val === "object" ? JSON.stringify(val) : String(val);
    parts.push(field === "non_field_errors" ? text : `${LABELS[field] || field}: ${text}`);
  }
  return parts.join(" · ") || "Solicitud inválida.";
}

const LABELS = { email: "Email", password: "Contraseña", title: "Asunto", description: "Descripción", body: "Mensaje",
  first_name: "Nombre", last_name: "Apellido", question: "Pregunta", status: "Estado", priority: "Prioridad" };

function csrfToken() {
  const m = document.cookie.match(/(?:^|; )csrftoken=([^;]*)/);
  return m ? decodeURIComponent(m[1]) : "";
}

export async function api(method, path, body) {
  const headers = { Accept: "application/json" };
  const opts = { method, credentials: "same-origin", headers };
  if (body !== undefined) { headers["Content-Type"] = "application/json"; opts.body = JSON.stringify(body); }
  if (method !== "GET") headers["X-CSRFToken"] = csrfToken();
  let res;
  try { res = await fetch("/api" + path, opts); }
  catch { throw new ApiError(0, null); }
  if (res.status === 204) return null;
  let data = null;
  try { data = await res.json(); } catch { /* sin cuerpo JSON */ }
  if (!res.ok) {
    if (res.status === 401 && !path.startsWith("/auth/")) window.dispatchEvent(new Event("unauthorized"));
    throw new ApiError(res.status, data);
  }
  return data;
}

export const get = (path) => api("GET", path);
export const post = (path, body = {}) => api("POST", path, body);
export const patch = (path, body) => api("PATCH", path, body);

export function qs(params) {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    if (Array.isArray(v)) v.forEach((x) => sp.append(k, x)); else sp.set(k, v);
  }
  const s = sp.toString();
  return s ? "?" + s : "";
}
