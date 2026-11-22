import { get } from "./api.js";
import { clear, h, toast } from "./dom.js";
import { ensureShell, resetShell, setActive } from "./layout.js";
import { state } from "./state.js";
import * as auth from "./views/auth.js";
import * as dashboard from "./views/dashboard.js";
import * as tickets from "./views/tickets.js";
import * as ticketDetail from "./views/ticketDetail.js";
import * as newTicket from "./views/newTicket.js";
import * as kb from "./views/knowledge.js";

const root = document.getElementById("app");
let cleanup = null;
let seq = 0;

const ROUTES = [
  [/^\/login$/, auth.renderLogin, null, true],
  [/^\/register$/, auth.renderRegister, null, true],
  [/^\/dashboard$/, dashboard.render, "dashboard"],
  [/^\/tickets$/, tickets.render, "tickets"],
  [/^\/tickets\/(\d+)$/, ticketDetail.render, "tickets"],
  [/^\/new$/, newTicket.render, "tickets"],
  [/^\/kb$/, kb.renderList, "kb"],
  [/^\/kb\/new$/, kb.renderEditor, "kb"],
  [/^\/kb\/(\d+)\/edit$/, kb.renderEditor, "kb"],
  [/^\/kb\/(\d+)$/, kb.renderArticle, "kb"],
];

function parseHash() {
  const raw = location.hash.replace(/^#/, "") || "/dashboard";
  const [path, query = ""] = raw.split("?");
  return { path, query: new URLSearchParams(query) };
}

async function route() {
  const my = ++seq;
  if (cleanup) { try { cleanup(); } catch { /* noop */ } cleanup = null; }
  const { path, query } = parseHash();
  const match = ROUTES.map(([re, fn, key, pub]) => [re.exec(path), fn, key, pub]).find(([m]) => m);

  if (!match) { location.hash = state.user ? "#/dashboard" : "#/login"; return; }
  const [m, fn, key, isPublic] = match;
  if (!state.user && !isPublic) { location.hash = "#/login"; return; }
  if (state.user && isPublic) { location.hash = "#/dashboard"; return; }

  if (isPublic) {
    resetShell(); clear(root);
    document.title = "Whodesk · Ingresar";
    cleanup = await fn(root, { query });
    return;
  }
  const shell = ensureShell(root);
  setActive(key);
  clear(shell.content);
  shell.content.append(h("div", { class: "loading" }, "Cargando…"));
  try {
    const box = h("div", {});
    const result = await fn(box, { params: m.slice(1), query, shell });
    if (my !== seq) { if (typeof result === "function") result(); return; } // el usuario ya navegó a otra ruta
    clear(shell.content); shell.content.append(...box.childNodes);
    cleanup = typeof result === "function" ? result : null;
    window.scrollTo(0, 0);
    const af = shell.content.querySelector("[data-autofocus]");
    if (af) { af.focus(); af.setSelectionRange?.(af.value.length, af.value.length); }
  } catch (err) {
    if (my !== seq) return;
    clear(shell.content);
    shell.content.append(h("div", { class: "card empty" }, h("h2", {}, err.status === 404 ? "No encontramos lo que buscás" : "Algo salió mal"),
      h("p", {}, err.status === 404 ? "El recurso no existe o no tenés acceso." : err.message), h("a", { class: "btn", href: "#/dashboard" }, "Volver al panel")));
  }
}

window.addEventListener("hashchange", route);
window.addEventListener("unauthorized", () => {
  if (state.user) { state.user = null; resetShell(); toast("Tu sesión expiró. Ingresá de nuevo.", "error"); }
  location.hash = "#/login";
});

(async function boot() {
  try { state.user = await get("/users/me/"); } catch { state.user = null; }
  await route();
})();
