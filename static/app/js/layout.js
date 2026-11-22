import { post } from "./api.js";
import { clear, h, icon, toast } from "./dom.js";
import { avatar, ROLE } from "./format.js";
import { isAdmin, state } from "./state.js";
import { mountAssistant } from "./components/assistant.js";

let shell = null;

function navItem(href, iconName, label, key) {
  return h("a", { href, "data-key": key }, icon(iconName), label);
}

export function setActive(key) {
  const params = new URLSearchParams(location.hash.split("?")[1] || "");
  const statuses = params.getAll("status");
  const queue = params.get("assigned_to") === "unassigned" ? "queue-unassigned"
    : params.get("assigned_to") === "me" ? "queue-mine"
      : statuses.length === 1 && statuses[0] === "waiting_customer" ? "queue-waiting" : null;
  document.querySelectorAll(".nav a").forEach((a) =>
    a.classList.toggle("active", queue ? a.dataset.key === queue : a.dataset.key === key));
  const currentShell = document.querySelector(".shell");
  currentShell?.classList.remove("nav-open");
  currentShell?.classList.toggle("list-active", /^#\/tickets(?:\?.*)?$/.test(location.hash));
  currentShell?.classList.toggle("new-active", /^#\/new(?:\?.*)?$/.test(location.hash));
}

export function ensureShell(root) {
  if (shell && root.contains(shell.el)) return shell;
  clear(root);
  const searchInput = h("input", { type: "search", placeholder: "Buscar tickets…", "aria-label": "Buscar tickets",
    onkeydown: (e) => {
      if (e.key === "Enter" && e.target.value.trim()) location.hash = `#/tickets?search=${encodeURIComponent(e.target.value.trim())}`;
    } });
  const menu = h("div", { class: "usermenu", hidden: true },
    h("div", { class: "who" }, h("strong", {}, state.user.full_name), h("small", {}, `${state.user.email} · ${ROLE[state.user.role]}`)),
    isAdmin() ? h("a", { href: "/admin/", target: "_blank", rel: "noopener" }, icon("settings"), "Administración (Django)") : null,
    h("a", { href: "/api/docs/", target: "_blank", rel: "noopener" }, icon("book"), "Documentación de la API"),
    h("button", { type: "button", onclick: async () => {
      try { await post("/auth/logout/"); } catch { /* sesión ya cerrada */ }
      state.user = null; shell = null; location.hash = "#/login"; toast("Sesión cerrada");
    } }, icon("logout"), "Cerrar sesión"));
  const userBtn = h("button", { class: "btn btn-ghost", type: "button", "aria-label": "Menú de usuario", onclick: (e) => { e.stopPropagation(); menu.hidden = !menu.hidden; } },
    avatar(state.user, 32));
  document.addEventListener("click", () => { menu.hidden = true; });

  const content = h("main", { class: "content", id: "content", tabindex: "-1" });
  const el = h("div", { class: "shell" },
    h("aside", { class: "sidebar" },
      h("div", { class: "brand" }, h("span", { class: "brand-mark", "aria-hidden": "true" }, "?"), "Whodesk"),
      h("nav", { class: "nav", "aria-label": "Principal" },
        h("div", { class: "nav-label" }, "Espacio"),
        navItem("#/dashboard", "home", "Panel", "dashboard"),
        navItem("#/tickets", "ticket", state.user.role === "customer" ? "Mis tickets" : "Todos los tickets", "tickets"),
        navItem("#/kb", "book", "Base de conocimiento", "kb"),
        state.user.role !== "customer" ? h("div", { class: "nav-label" }, "Bandeja de trabajo") : null,
        state.user.role !== "customer" ? [
          navItem("#/tickets?status=open&status=in_progress&status=waiting_customer&assigned_to=unassigned", "ticket", "Sin asignar", "queue-unassigned"),
          navItem("#/tickets?status=open&status=in_progress&status=waiting_customer&assigned_to=me", "user", "Asignados a mí", "queue-mine"),
          navItem("#/tickets?status=waiting_customer", "message", "Esperando al cliente", "queue-waiting"),
        ] : null),
      h("div", { class: "sidebar-foot" }, "Proyecto de portfolio · datos de demostración")),
    h("div", { class: "main" },
      h("header", { class: "topbar" },
        h("button", { class: "btn btn-ghost icon-btn menu-btn", type: "button", "aria-label": "Abrir menú",
          onclick: () => document.querySelector(".shell").classList.toggle("nav-open") }, icon("menu", 20)),
        h("div", { class: "search" }, icon("search", 16), searchInput),
        h("span", { class: "spacer" }),
        h("a", { class: "btn btn-primary", href: "#/new" }, icon("plus", 16), "Nuevo ticket"),
        h("div", { class: "userbox" }, userBtn, menu)),
      content));
  root.append(el);
  mountAssistant(root);
  shell = { el, content, searchInput };
  return shell;
}

export function resetShell() { shell = null; }
