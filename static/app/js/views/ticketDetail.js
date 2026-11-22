import { get, post, patch } from "../api.js";
import { clear, h, icon, modal, toast } from "../dom.js";
import { avatar, describeEvent, fmtDate, PRIORITY, priorityTag, ROLE, statusBadge, timeAgo } from "../format.js";
import { isStaff, state } from "../state.js";

function actionLabel(from, to, staff) {
  if (to === "in_progress") return from === "open" ? "Tomar ticket" : from === "resolved" ? "Reabrir ticket" : staff ? "Retomar" : "Ya respondí";
  if (to === "waiting_customer") return "Esperar respuesta del cliente";
  if (to === "resolved") return "Resolver…";
  if (to === "closed") return from === "resolved" ? (staff ? "Cerrar ticket" : "Confirmar y cerrar") : staff ? "Cerrar ticket" : "Cancelar ticket";
  return to;
}

export async function render(root, { params }) {
  const id = params[0];
  const staff = isStaff();
  let data = await load();
  let mode = "reply"; // "reply" | "note"
  let contextOpen = true;
  let draft = "";
  let replyTarget = null;
  let suggestion = null;
  const view = h("div", {});
  root.append(view);
  draw();
  document.title = `Whodesk · #${id} ${data.ticket.title}`;

  async function load() {
    const base = `/tickets/${id}`;
    const [ticket, comments, events, staffUsers, categories] = await Promise.all([
      get(base + "/"), get(base + "/comments/"), get(base + "/events/"),
      staff ? get("/users/staff/") : null, staff ? get("/categories/") : null]);
    return { ticket, comments, events, staffUsers, categories };
  }

  async function reload() { data = await load(); draw(); }
  async function act(fn, okMsg, placement = "top-right") {
    try { await fn(); if (okMsg) toast(okMsg, "ok", placement); await reload(); }
    catch (e) { toast(e.message, "error"); }
  }

  function transition(to) {
    const t = data.ticket;
    if (to === "resolved") {
      const note = h("textarea", { placeholder: "Qué se hizo para resolverlo (esta nota alimenta la base de conocimiento).", rows: 5, "aria-label": "Nota de resolución" });
      return modal({ title: "Resolver ticket", body: h("div", { class: "field" }, h("label", {}, "Nota de resolución (obligatoria)"), note),
        confirmText: "Marcar como resuelto",
        onConfirm: async () => { await post(`/tickets/${id}/transition/`, { status: "resolved", resolution_note: note.value }); } })
        .then((r) => { if (r) { toast("Ticket resuelto"); return reload(); } });
    }
    return act(async () => {
      await post(`/tickets/${id}/transition/`, { status: to });
      if (to === "closed") replyTarget = null;
    },
      to === "closed" ? "Ticket cerrado" : "Estado actualizado", to === "closed" ? "bottom-center" : "top-right");
  }

  async function sendComment() {
    const message = draft.trim();
    if (!message) return toast("Escribí un mensaje primero.", "error");
    const excerpt = replyTarget?.body.replace(/\s+/g, " ").trim() ?? "";
    const quote = excerpt.length > 180 ? `${excerpt.slice(0, 180).trimEnd()}…` : excerpt;
    const body = replyTarget
      ? `En respuesta a ${replyTarget.author} · ${replyTarget.reference}:\n“${quote}”\n\n${message}`
      : message;
    await act(async () => {
      await post(`/tickets/${id}/comments/`, { body, is_internal: mode === "note" });
      draft = ""; replyTarget = null; suggestion = null;
    }, mode === "note" ? "Nota privada guardada" : "Respuesta enviada");
  }

  function selectReply(author, body, reference) {
    mode = "reply";
    replyTarget = { author: author.full_name, body, reference };
    draw();
    view.querySelector(".composer textarea")?.focus();
  }

  async function suggest() {
    suggestion = { loading: true }; draw();
    try { suggestion = await post(`/tickets/${id}/suggest-reply/`); }
    catch (e) { suggestion = null; toast(e.message, "error"); }
    draw();
  }

  async function feedback(value) {
    try { await post(`/assistant/queries/${suggestion.query_id}/feedback/`, { value }); toast("¡Gracias por tu opinión!"); suggestion.rated = value; draw(); }
    catch (e) { toast(e.message, "error"); }
  }

  function bubble(author, body, when, { internal = false, first = false, reference = "" } = {}) {
    const isStaffAuthor = author.role !== "customer";
    return h("article", { class: "msg" }, avatar(author, 34),
      h("div", { class: "msg-content" },
        h("div", { class: `bubble ${internal ? "internal" : isStaffAuthor ? "staff" : ""}` },
          h("div", { class: "bubble-head" }, h("strong", {}, author.full_name), h("span", { class: "chip" }, ROLE[author.role]),
            internal ? h("span", { class: "private-tag" }, icon("lock", 13), "Nota privada") : null,
            h("span", { class: "when" }, first ? `Creó el ticket · ${fmtDate(when)}` : fmtDate(when))),
          h("div", { class: "body-text" }, body)),
        internal || data.ticket.status === "closed" ? null : h("button", { class: "reply-link", type: "button",
          "aria-label": `Responder a ${author.full_name}, ${reference}`,
          onclick: () => selectReply(author, body, reference) }, icon("reply", 15), `Responder a ${author.full_name} · ${reference}`)));
  }

  function aiBox() {
    if (!suggestion) return null;
    if (suggestion.loading) return h("div", { class: "ai-box" }, h("h3", {}, icon("sparkles", 15), "Buscando en la base de conocimiento…"),
      h("div", { class: "skeleton", style: "width:90%" }), h("div", { class: "skeleton", style: "width:70%" }));
    const s = suggestion;
    const draftBtn = h("button", { class: "btn btn-sm btn-primary", type: "button", onclick: () => { draft = s.answer; mode = "reply"; suggestion = null; draw(); } }, "Usar como borrador");
    return h("div", { class: "ai-box" },
      h("h3", {}, icon("sparkles", 15), s.abstained ? "Sin sugerencia" : s.mode === "llm" ? "Respuesta sugerida por IA" : "Fragmento relevante (sin IA generativa)"),
      h("div", { class: "body-text" }, s.answer),
      s.notice ? h("div", { class: "t-sub", style: "margin-top:6px" }, s.notice) : null,
      s.sources.length ? h("div", { class: "sources" }, s.sources.map((src, i) => h("a", { class: "source",
        href: src.type === "article" ? `#/kb/${src.id}` : `#/tickets/${src.id}`, title: src.excerpt }, icon(src.type === "article" ? "book" : "ticket", 13), `[${i + 1}] ${src.title}`))) : null,
      h("div", { class: "ai-actions" }, s.abstained ? null : draftBtn,
        h("span", { class: "t-sub" }, "Revisá siempre antes de enviar."),
        h("span", { style: "margin-left:auto;display:flex;gap:4px" },
          h("button", { class: "btn btn-sm btn-ghost icon-btn", type: "button", "aria-label": "Útil", disabled: s.rated != null, onclick: () => feedback(1) }, icon("up", 15)),
          h("button", { class: "btn btn-sm btn-ghost icon-btn", type: "button", "aria-label": "No útil", disabled: s.rated != null, onclick: () => feedback(-1) }, icon("down", 15)),
          h("button", { class: "btn btn-sm btn-ghost icon-btn", type: "button", "aria-label": "Descartar", onclick: () => { suggestion = null; draw(); } }, icon("x", 15)))));
  }

  function composer() {
    const t = data.ticket;
    if (t.status === "closed") return h("div", { class: "card card-pad t-sub" }, "Este ticket está cerrado. Creá uno nuevo si el problema continúa.");
    const ta = h("textarea", { placeholder: mode === "note" ? "Escribí una nota visible solo para el equipo…" : "Escribí tu respuesta…",
      "aria-label": "Mensaje", value: draft, oninput: (e) => { draft = e.target.value; } });
    return h("div", {}, aiBox(),
      h("div", { class: `card composer ${mode === "note" ? "is-note" : ""}` },
        staff ? h("div", { class: "tabs", role: "tablist" },
          h("button", { class: `tab ${mode === "reply" ? "active" : ""}`, type: "button", onclick: () => { mode = "reply"; draw(); } }, "Responder"),
          h("button", { class: `tab ${mode === "note" ? "active" : ""}`, type: "button", onclick: () => { mode = "note"; draw(); } }, "Nota privada")) : null,
        replyTarget ? h("div", { class: "reply-context", role: "status" },
          h("div", { class: "reply-context-copy" },
            h("strong", {}, `Respondiendo a ${replyTarget.author}`),
            h("span", {}, replyTarget.reference),
            h("p", {}, replyTarget.body.length > 180 ? `${replyTarget.body.slice(0, 180).trimEnd()}…` : replyTarget.body)),
          h("button", { class: "reply-cancel", type: "button", "aria-label": "Quitar referencia de respuesta",
            onclick: () => { replyTarget = null; draw(); } }, icon("x", 16))) : null,
        ta,
        h("div", { class: "composer-foot" },
          staff ? h("button", { class: "btn btn-ai btn-sm", type: "button", disabled: suggestion?.loading, onclick: suggest }, icon("sparkles", 15), "Sugerir con IA") : h("span"),
          h("button", { class: "btn btn-primary btn-sm", type: "button", onclick: sendComment }, icon("send", 15), mode === "note" ? "Guardar nota" : "Enviar"))));
  }

  function selectField(label, value, options, onchange) {
    return h("div", { class: "prop" }, h("div", { class: "prop-label" }, label),
      h("select", { "aria-label": label, value: value ?? "", onchange: (e) => onchange(e.target.value) }, options.map(([v, l]) => h("option", { value: v }, l))));
  }

  function side() {
    const t = data.ticket;
    const actions = t.allowed_transitions.map((to) => h("button", {
      class: `btn ${to === "resolved" || (to === "in_progress" && t.status === "open") ? "btn-primary" : ""}`, type: "button",
      onclick: () => transition(to) }, actionLabel(t.status, to, staff)));
    const props = staff ? [
      selectField("Prioridad", t.priority, Object.entries(PRIORITY), (v) => act(() => patch(`/tickets/${id}/`, { priority: v }), "Prioridad actualizada")),
      selectField("Asignado a", t.assigned_to?.id ?? "", [["", "Sin asignar"], ...data.staffUsers.map((u) => [u.id, u.full_name])],
        (v) => act(() => post(`/tickets/${id}/assign/`, { assigned_to: v === "" ? null : Number(v) }), "Asignación actualizada")),
      selectField("Categoría", t.category?.id ?? "", [["", "Sin categoría"], ...data.categories.map((c) => [c.id, c.name])],
        (v) => act(() => patch(`/tickets/${id}/`, { category: v === "" ? null : Number(v) }), "Categoría actualizada")),
    ] : [
      h("div", { class: "prop" }, h("div", { class: "prop-label" }, "Prioridad"), priorityTag(t.priority)),
      h("div", { class: "prop" }, h("div", { class: "prop-label" }, "Asignado a"), t.assigned_to ? t.assigned_to.full_name : h("span", { class: "t-sub" }, "En espera de un agente")),
      t.category ? h("div", { class: "prop" }, h("div", { class: "prop-label" }, "Categoría"), h("span", { class: "chip" }, t.category.name)) : null,
    ];
    return h("aside", { class: "ticket-context", id: `ticket-context-${id}` },
      h("div", { class: "card side-card" }, h("div", { class: "card-head" }, h("h2", {}, "Estado"), statusBadge(t.status)),
        h("div", { class: "side-body" }, actions.length ? h("div", { class: "actions", style: "margin-top:0" }, actions) : h("span", { class: "t-sub" }, "No hay acciones disponibles."))),
      h("div", { class: "card side-card" }, h("div", { class: "card-head" }, h("h2", {}, "Datos del ticket")), h("div", { class: "side-body" }, props,
        h("div", { class: "prop" }, h("div", { class: "prop-label" }, "Solicitante"), h("span", { class: "person" }, avatar(t.created_by, 26), t.created_by.full_name)),
        h("div", { class: "prop" }, h("div", { class: "prop-label" }, "Creado"), fmtDate(t.created_at)))),
      h("div", { class: "card side-card" }, h("div", { class: "card-head" }, h("h2", {}, "Actividad")),
        h("div", { class: "side-body" }, h("ul", { class: "timeline" }, data.events.map((e) =>
          h("li", {}, describeEvent(e), h("span", { class: "when" }, timeAgo(e.created_at))))))));
  }

  function draw() {
    const t = data.ticket;
    clear(view);
    view.append(
      h("div", { class: "crumbs" }, h("a", { href: "#/tickets" }, "Tickets"), icon("chevron", 14), `#${t.id}`),
      h("div", { class: `detail ${contextOpen ? "" : "context-collapsed"}` },
        h("section", {},
          h("h1", { class: "ticket-title" }, t.title),
          h("div", { class: "meta-line" }, statusBadge(t.status), priorityTag(t.priority), t.category ? h("span", { class: "chip" }, t.category.name) : null,
            h("span", {}, `Actualizado ${timeAgo(t.updated_at)}`),
            h("button", { class: "btn btn-sm btn-context", type: "button", "aria-controls": `ticket-context-${id}`,
              "aria-expanded": String(contextOpen),
              onclick: (e) => {
                contextOpen = !contextOpen;
                view.querySelector(".detail")?.classList.toggle("context-collapsed", !contextOpen);
                e.currentTarget.setAttribute("aria-expanded", String(contextOpen));
                e.currentTarget.textContent = contextOpen ? "Ocultar datos" : "Ver datos";
              } }, contextOpen ? "Ocultar datos" : "Ver datos")),
          t.status === "resolved" || (t.status === "closed" && t.resolution_note)
            ? h("div", { class: "resolution" }, h("strong", {}, "Nota de resolución"), h("div", { class: "body-text" }, t.resolution_note)) : null,
          h("div", { class: "thread" }, bubble(t.created_by, t.description, t.created_at,
            { first: true, reference: `ticket #${t.id} · consulta inicial` }),
            data.comments.map((c) => bubble(c.author, c.body, c.created_at, { internal: c.is_internal, reference: `mensaje #${c.id}` }))),
          composer()),
        side()));
  }
}
