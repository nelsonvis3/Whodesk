import { get, qs } from "../api.js";
import { h, icon } from "../dom.js";
import { PRIORITY, STATUS } from "../format.js";
import { ticketRow } from "../components/ticketRow.js";
import { isStaff } from "../state.js";

const STATES = [["", "Cualquier estado"], ...Object.entries(STATUS)];

export async function render(root, { query }) {
  document.title = "Whodesk · Tickets";
  const statuses = query.getAll("status");
  const f = { status: statuses, priority: query.get("priority") || "", assigned_to: query.get("assigned_to") || "",
    search: query.get("search") || "", page: Number(query.get("page") || 1) };
  const staff = isStaff();
  const resultsList = h("div", { class: "ticket-results-list" });
  const resultCount = h("p", { class: "results-count", "aria-live": "polite", "aria-atomic": "true" }, "Cargando solicitudes…");

  const go = (patch) => {
    const next = { ...f, page: 1, ...patch };
    location.hash = "#/tickets" + qs({ status: next.status, priority: next.priority, assigned_to: next.assigned_to, search: next.search, page: next.page > 1 ? next.page : "" });
  };
  const field = (id, label, control, extraClass = "") => h("div", { class: `filter-field ${extraClass}`.trim() },
    h("label", { for: id }, label), control);

  const search = h("input", { id: "ticket-search", type: "search", placeholder: "Asunto o descripción", value: f.search,
    "aria-label": "Buscar por asunto o descripción" });
  const searchForm = h("form", { class: "filter-search-form", onsubmit: (e) => {
    e.preventDefault(); go({ search: search.value.trim() });
  } }, search, h("button", { class: "btn btn-primary", type: "submit" }, "Buscar"));
  const status = h("select", { id: "ticket-status", value: statuses.length === 1 ? statuses[0] : "",
    onchange: (e) => go({ status: e.target.value ? [e.target.value] : [] }) },
    STATES.map(([value, label]) => h("option", { value }, label)));
  const prio = h("select", { id: "ticket-priority", onchange: (e) => go({ priority: e.target.value }), value: f.priority },
    h("option", { value: "" }, "Todas las prioridades"), Object.entries(PRIORITY).map(([k, v]) => h("option", { value: k }, v)));
  const assignee = staff ? h("select", { id: "ticket-assignee", onchange: (e) => go({ assigned_to: e.target.value }), value: f.assigned_to },
    h("option", { value: "" }, "Cualquier responsable"), h("option", { value: "me" }, "Asignados a mí"), h("option", { value: "unassigned" }, "Sin asignar")) : null;

  root.append(
    h("div", { class: "page-head" }, h("div", {}, h("h1", {}, staff ? "Tickets" : "Mis tickets"),
      h("p", {}, "Cada solicitud muestra por separado su estado, responsable y última actividad."))),
    h("section", { class: "filters-panel", "aria-labelledby": "filters-title" },
      h("div", { class: "filters-head" }, h("h2", { id: "filters-title" }, "Buscar y filtrar"),
        h("p", {}, "Elegí un criterio para encontrar una solicitud.")),
      h("div", { class: `filters-grid ${staff ? "staff" : "customer"}` },
        field("ticket-search", "Buscar por asunto o descripción", searchForm, "filter-field-search"),
        field("ticket-status", "Estado", status), field("ticket-priority", "Prioridad", prio),
        assignee ? field("ticket-assignee", "Responsable", assignee) : null),
      h("div", { class: "filter-actions" }, h("button", { class: "btn btn-ghost", type: "button", onclick: () => { location.hash = "#/tickets"; } }, "Restablecer filtros"))),
    h("div", { class: "results-head" }, h("h2", {}, staff ? "Solicitudes" : "Mis solicitudes"), resultCount),
    resultsList);

  async function load() {
    const params = { page: f.page, status: f.status, priority: f.priority, assigned_to: f.assigned_to, search: f.search, ordering: "-updated_at", page_size: 15 };
    const data = await get("/tickets/" + qs(params));
    resultsList.replaceChildren();
    resultCount.textContent = `${data.count} ${data.count === 1 ? "solicitud" : "solicitudes"}`;
    if (!data.results.length) {
      resultsList.append(h("div", { class: "empty" }, icon("ticket", 44), h("h3", {}, "No hay solicitudes con estos filtros"),
        h("p", {}, "Probá cambiar o restablecer los filtros para ver otros tickets.")));
      return;
    }
    const rows = data.results.map(ticketRow);
    const pages = Math.max(1, Math.ceil(data.count / 15));
    resultsList.append(
      h("ul", { class: "ticket-list", "aria-label": staff ? "Solicitudes de soporte" : "Mis solicitudes de soporte" }, rows),
      h("nav", { class: "pager", "aria-label": "Paginación de solicitudes" },
        h("span", {}, `Página ${f.page} de ${pages}`),
        h("div", { class: "pager-controls" },
          h("button", { class: "btn btn-sm", type: "button", disabled: !data.previous, onclick: () => go({ page: f.page - 1 }) }, "Anterior"),
          h("button", { class: "btn btn-sm", type: "button", disabled: !data.next, onclick: () => go({ page: f.page + 1 }) }, "Siguiente"))));
  }
  await load();
}
