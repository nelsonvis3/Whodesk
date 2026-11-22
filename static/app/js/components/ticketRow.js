import { h } from "../dom.js";
import { priorityTag, statusBadge, timeAgo } from "../format.js";

function detail(label, value, extraClass = "") {
  return h("div", { class: "ticket-detail" },
    h("span", { class: "ticket-detail-label" }, label),
    h("span", { class: `ticket-detail-value ${extraClass}`.trim() }, value));
}

export function ticketRow(ticket) {
  const requester = ticket.created_by?.full_name || "Solicitante";
  const category = ticket.category?.name || "Sin categoría";
  const assignee = ticket.assigned_to?.full_name || "Sin asignar";
  const updatedAt = new Date(ticket.updated_at);

  return h("li", { class: "ticket-list-item" },
    h("a", { class: `ticket-card status-${ticket.status}`, href: "#/tickets/" + ticket.id },
      h("div", { class: "ticket-card-heading" },
        h("span", { class: "ticket-code" }, `Ticket #${ticket.id}`),
        h("div", { class: "ticket-signals" }, statusBadge(ticket.status), priorityTag(ticket.priority))),
      h("h3", { class: "ticket-title" }, ticket.title || "Solicitud sin título"),
      h("div", { class: "ticket-details" },
        detail("Solicitante", requester),
        detail("Categoría", category),
        detail("Responsable", assignee),
        h("div", { class: "ticket-detail" },
          h("span", { class: "ticket-detail-label" }, "Última actividad"),
          h("time", { class: "ticket-detail-value ticket-updated", dateTime: ticket.updated_at,
            title: updatedAt.toLocaleString("es-AR") }, timeAgo(ticket.updated_at))))));
}
