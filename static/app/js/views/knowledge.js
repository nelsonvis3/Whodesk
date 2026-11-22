import { get, patch, post, qs } from "../api.js";
import { append, debounce, h, icon, toast } from "../dom.js";
import { fmtDate } from "../format.js";
import { isAdmin } from "../state.js";

export async function renderList(root, { query }) {
  document.title = "Whodesk · Base de conocimiento";
  const q = query.get("q") || "";
  const grid = h("div", { class: "kb-grid" });
  const search = h("input", { type: "search", value: q, placeholder: "Buscar artículos…", "aria-label": "Buscar artículos", "data-autofocus": q ? "1" : null,
    oninput: debounce((e) => { location.hash = "#/kb" + qs({ q: e.target.value.trim() }); }, 400) });
  root.append(
    h("div", { class: "page-head" }, h("div", {}, h("h1", {}, "Base de conocimiento"), h("p", {}, "Guías y respuestas a las consultas más frecuentes.")),
      isAdmin() ? h("a", { class: "btn btn-primary", href: "#/kb/new" }, icon("plus", 16), "Nuevo artículo") : null),
    h("div", { class: "search", style: "max-width:520px;margin-bottom:18px" }, icon("search", 16), search), grid);
  const data = await get("/knowledge/articles/" + qs({ search: q, page_size: 60 }));
  if (!data.results.length) {
    grid.replaceWith(h("div", { class: "card empty" }, icon("book", 44), h("h3", {}, "No encontramos artículos"), h("p", {}, "Probá con otras palabras o creá un ticket.")));
    return;
  }
  append(grid, data.results.map((a) => h("a", { class: "card kb-card", href: `#/kb/${a.id}` },
    h("h3", {}, a.title, a.is_public ? null : h("span", { class: "chip", style: "margin-left:8px" }, "Interno"),
      a.is_active ? null : h("span", { class: "chip", style: "margin-left:8px" }, "Inactivo")), h("p", {}, a.excerpt))));
}

export async function renderArticle(root, { params }) {
  const a = await get(`/knowledge/articles/${params[0]}/`);
  document.title = `Whodesk · ${a.title}`;
  root.append(
    h("div", { class: "crumbs" }, h("a", { href: "#/kb" }, "Base de conocimiento"), icon("chevron", 14), a.title),
    h("article", { class: "card card-pad article" },
      h("h1", {}, a.title),
      h("div", { class: "meta-line" }, `Actualizado ${fmtDate(a.updated_at)}`, a.is_public ? null : h("span", { class: "chip" }, "Solo equipo interno"),
        isAdmin() ? h("a", { class: "btn btn-sm", href: `#/kb/${a.id}/edit` }, "Editar") : null),
      a.body.split(/\n\s*\n/).map((p) => h("p", {}, p)),
      h("hr", { style: "border:0;border-top:1px solid var(--border);margin:22px 0" }),
      h("p", { class: "t-sub" }, "¿No resolvió tu consulta? ", h("a", { href: `#/new?title=${encodeURIComponent(a.title)}` }, "Creá un ticket"), ".")));
}

export async function renderEditor(root, { params }) {
  if (!isAdmin()) { location.hash = "#/kb"; return; }
  const id = params[0];
  const a = id ? await get(`/knowledge/articles/${id}/`) : { title: "", body: "", is_public: true, is_active: true };
  document.title = "Whodesk · Editar artículo";
  const err = h("div", { class: "error-box", hidden: true, role: "alert" });
  const title = h("input", { id: "t", type: "text", required: true, maxlength: 200, value: a.title });
  const body = h("textarea", { id: "b", rows: 14, required: true, value: a.body });
  const pub = h("input", { id: "p", type: "checkbox", checked: a.is_public });
  const act = h("input", { id: "a", type: "checkbox", checked: a.is_active });
  const btn = h("button", { class: "btn btn-primary", type: "submit" }, "Guardar");
  root.append(h("div", { class: "page-head" }, h("h1", {}, id ? "Editar artículo" : "Nuevo artículo")),
    h("form", { class: "card card-pad", style: "max-width:820px", onsubmit: async (e) => {
      e.preventDefault(); err.hidden = true; btn.disabled = true;
      const payload = { title: title.value, body: body.value, is_public: pub.checked, is_active: act.checked };
      try { const saved = id ? await patch(`/knowledge/articles/${id}/`, payload) : await post("/knowledge/articles/", payload);
        toast("Artículo guardado"); location.hash = `#/kb/${saved.id}`; }
      catch (ex) { err.textContent = ex.message; err.hidden = false; btn.disabled = false; }
    } }, err,
      h("div", { class: "field" }, h("label", { for: "t" }, "Título"), title),
      h("div", { class: "field" }, h("label", { for: "b" }, "Contenido"), body, h("span", { class: "hint" }, "Separá los párrafos con una línea en blanco: así se indexan mejor para el asistente.")),
      h("div", { class: "field" }, h("label", { class: "check" }, pub, "Público (visible para clientes y para el asistente)")),
      h("div", { class: "field" }, h("label", { class: "check" }, act, "Activo")),
      h("div", { style: "display:flex;gap:10px" }, btn, h("a", { class: "btn", href: id ? `#/kb/${id}` : "#/kb" }, "Cancelar"))));
}
