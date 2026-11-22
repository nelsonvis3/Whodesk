// Widget flotante del asistente de IA: responde con la base de conocimiento y muestra sus fuentes.
import { post } from "../api.js";
import { h, icon } from "../dom.js";

const SUGGESTIONS = ["¿Cómo restablezco mi contraseña?", "¿Cómo cambio de plan?", "¿Dónde descargo mis facturas?"];
let mounted = false;
let history = [];

function assistantMark() {
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("class", "assistant-mark");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  const defs = document.createElementNS(ns, "defs");
  const gradient = document.createElementNS(ns, "linearGradient");
  gradient.id = "whodesk-assistant-gradient";
  gradient.setAttribute("x1", "0%"); gradient.setAttribute("y1", "100%");
  gradient.setAttribute("x2", "100%"); gradient.setAttribute("y2", "0%");
  [["0%", "#4285F4"], ["34%", "#9B72CB"], ["66%", "#D96570"], ["84%", "#F6AE2D"], ["100%", "#34A853"]]
    .forEach(([offset, color]) => {
      const stop = document.createElementNS(ns, "stop");
      stop.setAttribute("offset", offset); stop.setAttribute("stop-color", color); gradient.append(stop);
    });
  defs.append(gradient);
  svg.append(defs);
  const star = document.createElementNS(ns, "path");
  star.setAttribute("d", "M12 1C13.7 7.7 16.3 10.3 23 12c-6.7 1.7-9.3 4.3-11 11C10.3 16.3 7.7 13.7 1 12 7.7 10.3 10.3 7.7 12 1Z");
  star.setAttribute("fill", "url(#whodesk-assistant-gradient)");
  svg.append(star);
  return svg;
}

export function mountAssistant(root) {
  if (mounted && document.querySelector(".assistant")) return;
  mounted = true;
  history = [];
  const body = h("div", { class: "as-body", "aria-live": "polite" });
  const input = h("input", { type: "text", maxlength: 500, placeholder: "Escribí tu consulta…", "aria-label": "Consulta al asistente" });
  const sendBtn = h("button", { class: "btn btn-primary icon-btn", type: "submit", "aria-label": "Enviar" }, icon("send", 16));
  const panel = h("section", { class: "assistant", id: "support-assistant-panel", hidden: true, role: "region", "aria-label": "Asistente de soporte" },
    h("div", { class: "as-head" }, icon("sparkles", 20), h("div", { class: "grow" }, h("strong", {}, "Asistente de soporte"), h("small", {}, "IA · responde con la base de conocimiento")),
      h("button", { class: "btn btn-ghost icon-btn", type: "button", "aria-label": "Cerrar", onclick: () => toggle(false) }, icon("x", 18))),
    body,
    h("form", { class: "as-foot", onsubmit: (e) => { e.preventDefault(); ask(input.value); } }, input, sendBtn));
  const fab = h("button", { class: "fab", type: "button", "aria-label": "Abrir asistente de soporte", "aria-controls": "support-assistant-panel",
    "aria-expanded": "false", onclick: () => toggle(true) }, assistantMark());

  function toggle(open) {
    panel.hidden = !open; fab.hidden = open; fab.setAttribute("aria-expanded", String(open));
    if (open) { if (!history.length) welcome(); input.focus(); }
    else fab.focus();
  }

  function scroll() { body.scrollTop = body.scrollHeight; }
  function userMsg(text) { body.append(h("div", { class: "as-msg user" }, text)); scroll(); }
  function welcome() {
    history.push("welcome");
    body.append(h("div", { class: "as-msg bot" }, "Hola 👋 Soy el asistente de soporte. Contame tu consulta y busco la respuesta en la base de conocimiento.",
      h("div", { class: "as-chips" }, SUGGESTIONS.map((s) => h("button", { class: "as-chip", type: "button", onclick: () => ask(s) }, s)))));
  }

  async function ask(question) {
    question = question.trim();
    if (!question) return;
    input.value = ""; sendBtn.disabled = true; input.disabled = true;
    userMsg(question);
    const typing = h("div", { class: "as-msg bot" }, h("div", { class: "skeleton", style: "width:160px" }), h("div", { class: "skeleton", style: "width:110px" }));
    body.append(typing); scroll();
    try {
      const r = await post("/assistant/ask/", { question });
      typing.replaceWith(botAnswer(r, question));
    } catch (e) {
      typing.replaceWith(h("div", { class: "as-msg bot" }, e.message || "No pude responder ahora. Probá de nuevo en un momento."));
    }
    sendBtn.disabled = false; input.disabled = false; input.focus(); scroll();
  }

  function botAnswer(r, question) {
    const rate = (v, box) => async () => {
      try { await post(`/assistant/queries/${r.query_id}/feedback/`, { value: v }); box.replaceChildren("¡Gracias por tu opinión!"); } catch { /* no crítico */ }
    };
    const fb = h("span", { class: "as-tag" });
    fb.append("¿Te sirvió? ",
      h("button", { class: "btn btn-sm btn-ghost icon-btn", type: "button", "aria-label": "Útil", onclick: rate(1, fb) }, icon("up", 14)),
      h("button", { class: "btn btn-sm btn-ghost icon-btn", type: "button", "aria-label": "No útil", onclick: rate(-1, fb) }, icon("down", 14)));
    return h("div", { class: "as-msg bot" }, r.answer,
      r.sources.length ? h("div", { class: "sources" }, r.sources.map((s) => h("a", { class: "source", href: `#/kb/${s.id}`, title: s.excerpt, onclick: () => toggle(false) },
        icon("book", 13), s.title))) : null,
      r.notice ? h("span", { class: "as-tag" }, r.notice) : null,
      r.abstained || r.mode === "extractive" ? null : h("span", { class: "as-tag" }, "Respuesta generada con IA. Verificá la información en los artículos citados."),
      fb,
      h("div", { class: "as-chips" }, h("a", { class: "as-chip", href: `#/new?title=${encodeURIComponent(question)}`, onclick: () => toggle(false) }, "Crear un ticket")));
  }

  root.append(fab, panel);
}
