import { get, post } from "../api.js";
import { debounce, h, icon, toast } from "../dom.js";
import { PRIORITY } from "../format.js";

export async function render(root, { query }) {
  document.title = "Whodesk · Nuevo ticket";
  const categories = await get("/categories/");
  const err = h("div", { class: "error-box", hidden: true, role: "alert" });
  const title = h("input", { id: "title", type: "text", maxlength: 200, required: true, value: query.get("title") || "", placeholder: "Resumen breve del problema" });
  const desc = h("textarea", { id: "desc", rows: 7, required: true, placeholder: "Contanos qué pasó, qué esperabas y qué pasos seguiste.", value: query.get("description") || "" });
  const cat = h("select", { id: "cat" }, h("option", { value: "" }, "Sin categoría"), categories.map((c) => h("option", { value: c.id }, c.name)));
  const prio = h("select", { id: "prio", value: "medium" }, Object.entries(PRIORITY).map(([k, v]) => h("option", { value: k }, v)));
  const btn = h("button", { class: "btn btn-primary", type: "submit" }, "Crear ticket");
  const deflect = h("div", { hidden: true });

  // Antes de crear el ticket, sugiere artículos relacionados (búsqueda barata, sin LLM).
  const suggest = debounce(async () => {
    const q = `${title.value} ${desc.value}`.trim();
    if (q.length < 8) { deflect.hidden = true; return; }
    try {
      const { results } = await get(`/assistant/search/?q=${encodeURIComponent(q)}`);
      deflect.replaceChildren();
      if (!results.length) { deflect.hidden = true; return; }
      deflect.hidden = false;
      deflect.append(h("div", { class: "deflect" }, h("h3", {}, icon("sparkles", 15), "¿Te sirve alguno de estos artículos?"),
        results.map((r) => h("a", { href: `#/kb/${r.id}` }, r.title, h("small", {}, r.excerpt)))));
    } catch { deflect.hidden = true; }
  }, 600);
  title.addEventListener("input", suggest); desc.addEventListener("input", suggest);
  if (title.value) suggest();

  const form = h("form", { onsubmit: async (e) => {
    e.preventDefault(); err.hidden = true; btn.disabled = true;
    try {
      const t = await post("/tickets/", { title: title.value, description: desc.value, priority: prio.value, category: cat.value ? Number(cat.value) : null });
      toast("Ticket creado"); location.hash = `#/tickets/${t.id}`;
    } catch (ex) { err.textContent = ex.message; err.hidden = false; btn.disabled = false; }
  } }, err,
    h("div", { class: "field" }, h("label", { for: "title" }, "Asunto"), title),
    deflect,
    h("div", { class: "field" }, h("label", { for: "desc" }, "Descripción"), desc),
    h("div", { class: "row" },
      h("div", { class: "field" }, h("label", { for: "cat" }, "Categoría"), cat),
      h("div", { class: "field" }, h("label", { for: "prio" }, "Prioridad"), prio)),
    h("div", { style: "display:flex;gap:10px" }, btn, h("a", { class: "btn", href: "#/tickets" }, "Cancelar")));

  root.append(h("div", { class: "page-head" }, h("div", {}, h("h1", {}, "Nuevo ticket"), h("p", {}, "Un agente te responderá en el horario de atención."))),
    h("div", { class: "card card-pad", style: "max-width:760px" }, form));
}
