import { get } from "../api.js";
import { h, icon } from "../dom.js";
import { STATUS } from "../format.js";
import { ticketRow } from "../components/ticketRow.js";
import { isStaff, state } from "../state.js";

const COLORS = { open: "var(--s-open)", in_progress: "var(--s-progress)", waiting_customer: "var(--s-wait)", resolved: "var(--s-resolved)", closed: "var(--s-closed)" };

function stat(label, value, href, color) {
  return h("a", { class: "card stat", href },
    h("div", { class: "lbl" }, h("span", { class: "dot", style: `background:${color}` }), label), h("div", { class: "num" }, value));
}

export async function render(root) {
  document.title = "Whodesk · Panel";
  const [stats, recent] = await Promise.all([get("/tickets/stats/"), get("/tickets/?page_size=8&ordering=-updated_at")]);
  const staff = isStaff();
  const visibleStatuses = staff ? ["open", "in_progress", "waiting_customer"] : ["open", "in_progress", "waiting_customer", "resolved"];
  const cards = visibleStatuses.map((s) =>
    stat(STATUS[s], stats.by_status[s], `#/tickets?status=${s}`, COLORS[s]));
  if (staff) {
    cards.push(stat("Sin asignar", stats.unassigned, "#/tickets?assigned_to=unassigned&status=open&status=in_progress&status=waiting_customer", "var(--p-urgent)"));
    cards.push(stat("Asignados a mí", stats.mine, "#/tickets?assigned_to=me&status=in_progress&status=waiting_customer&status=open", "var(--brand)"));
  }
  const rows = recent.results.map(ticketRow);

  root.append(
    h("div", { class: "page-head" }, h("div", {}, h("h1", {}, staff ? "Tu bandeja" : `Hola, ${state.user.first_name || state.user.email}`),
      h("p", {}, staff ? "Revisá los tickets que necesitan atención." : "Seguí el estado de tus consultas o abrí una nueva."))),
    h("div", { class: "stats" }, cards),
    h("div", { class: "card" },
      h("div", { class: "card-head" }, h("h2", {}, staff ? "Tickets recientes" : "Consultas recientes"), h("a", { href: "#/tickets" }, "Ver todos")),
      rows.length ? h("ul", { class: "ticket-list", "aria-label": staff ? "Tickets recientes" : "Mis tickets recientes" }, rows)
        : h("div", { class: "empty" }, icon("ticket", 40), h("p", {}, "Todavía no hay tickets."),
          h("a", { class: "btn btn-primary", href: "#/new" }, "Crear el primero"))));
}
