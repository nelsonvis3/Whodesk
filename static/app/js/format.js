import { h } from "./dom.js";

export const STATUS = {
  open: "Abierto", in_progress: "En progreso", waiting_customer: "Esperando al cliente", resolved: "Resuelto", closed: "Cerrado",
};
export const PRIORITY = { low: "Baja", medium: "Media", high: "Alta", urgent: "Urgente" };
export const ROLE = { customer: "Cliente", agent: "Agente", admin: "Administrador" };

export function statusBadge(status) {
  return h("span", { class: `badge s-${status}` }, STATUS[status] || status);
}

export function priorityTag(priority) {
  return h("span", { class: `prio p-${priority}` }, h("span", { class: "dot" }), PRIORITY[priority] || priority);
}

export function avatar(user, size = 30) {
  const name = user?.full_name || user?.email || "?";
  const initials = name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join("");
  return h("span", { class: "avatar", style: `background:#000;color:#fff;width:${size}px;height:${size}px;font-size:${Math.round(size * 0.4)}px`,
    title: name }, initials);
}

export function person(user) {
  if (!user) return h("span", { class: "t-sub" }, "Sin asignar");
  return h("span", { class: "person" }, avatar(user, 26), user.full_name);
}

const dateFmt = new Intl.DateTimeFormat("es-AR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
export const fmtDate = (iso) => (iso ? dateFmt.format(new Date(iso)) : "—");

export function timeAgo(iso) {
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "hace instantes";
  const m = s / 60; if (m < 60) return `hace ${Math.floor(m)} min`;
  const hr = m / 60; if (hr < 24) return `hace ${Math.floor(hr)} h`;
  const d = hr / 24; if (d < 30) return `hace ${Math.floor(d)} d`;
  return fmtDate(iso);
}

export function describeEvent(e) {
  const who = e.actor?.full_name || "Alguien";
  switch (e.event_type) {
    case "created": return `${who} creó el ticket`;
    case "status_changed": return `${who} cambió el estado: ${STATUS[e.from_value] || e.from_value} → ${STATUS[e.to_value] || e.to_value}`;
    case "assigned": return e.to_value ? `${who} asignó el ticket a ${e.to_value}` : `${who} quitó la asignación`;
    case "priority_changed": return `${who} cambió la prioridad: ${PRIORITY[e.from_value] || e.from_value} → ${PRIORITY[e.to_value] || e.to_value}`;
    case "category_changed": return `${who} cambió la categoría a ${e.to_value || "sin categoría"}`;
    case "commented": return e.to_value === "internal" ? `${who} dejó una nota privada` : `${who} respondió`;
    default: return `${who}: ${e.event_type}`;
  }
}
