// Utilidades de DOM. Nunca se usa innerHTML: todo texto entra como nodo de texto (anti-XSS).
const PROP_KEYS = new Set(["value", "checked", "selected", "disabled", "hidden"]);

export function h(tag, props = {}, ...children) {
  const el = document.createElement(tag);
  let pendingValue;
  for (const [k, v] of Object.entries(props || {})) {
    if (v === null || v === undefined) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2).toLowerCase(), v);
    else if (k === "value") pendingValue = v; // se asigna al final (los <select> necesitan sus <option>)
    else if (PROP_KEYS.has(k)) el[k] = Boolean(v);
    else if (v !== false) el.setAttribute(k, v === true ? "" : v);
  }
  append(el, children);
  if (pendingValue !== undefined) el.value = pendingValue;
  return el;
}

export function append(el, children) {
  for (const c of children.flat(Infinity)) {
    if (c === null || c === undefined || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}

export const clear = (el) => el.replaceChildren();

const ICONS = {
  home: "M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M9 22V12h6v10",
  ticket: "M22 12h-6l-2 3h-4l-2-3H2 M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z",
  book: "M4 19.5A2.5 2.5 0 0 1 6.5 17H20 M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z",
  plus: "M12 5v14 M5 12h14",
  search: "M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16z M21 21l-4.35-4.35",
  sparkles: "M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z M19 15l.9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9z",
  send: "M22 2L11 13 M22 2l-7 20-4-9-9-4 20-7z",
  x: "M18 6L6 18 M6 6l12 12",
  logout: "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4 M16 17l5-5-5-5 M21 12H9",
  user: "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2 M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
  up: "M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3",
  down: "M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17",
  lock: "M19 11H5a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7a2 2 0 0 0-2-2z M7 11V7a5 5 0 0 1 10 0v4",
  chevron: "M9 18l6-6-6-6",
  menu: "M3 12h18 M3 6h18 M3 18h18",
  check: "M20 6L9 17l-5-5",
  message: "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z",
  help: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3 M12 17h.01",
  reply: "M9 17l-5-5 5-5 M4 12h10a6 6 0 0 1 6 6v1",
  settings: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z",
};

export function icon(name, size = 18) {
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("width", size);
  svg.setAttribute("height", size);
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("class", "icon");
  for (const d of (ICONS[name] || "").split(" M")) {
    const p = document.createElementNS(ns, "path");
    p.setAttribute("d", d.startsWith("M") ? d : "M" + d);
    svg.append(p);
  }
  return svg;
}

export function toast(message, kind = "ok", placement = "top-right") {
  let box = document.querySelector(".toasts");
  if (!box) { box = h("div", { class: "toasts", role: "status", "aria-live": "polite" }); document.body.append(box); }
  box.classList.toggle("bottom-center", placement === "bottom-center");
  const t = h("div", { class: `toast ${kind === "error" ? "error" : ""}` }, message);
  box.append(t);
  setTimeout(() => t.remove(), 4200);
}

export function modal({ title, body, confirmText = "Confirmar", onConfirm, danger = false }) {
  return new Promise((resolve) => {
    const close = (v) => { overlay.remove(); document.removeEventListener("keydown", onKey); resolve(v); };
    const onKey = (e) => { if (e.key === "Escape") close(null); };
    const errorBox = h("div", { class: "error-box", hidden: true });
    const confirm = h("button", { class: `btn ${danger ? "btn-danger" : "btn-primary"}`, type: "button", onclick: async () => {
      if (!onConfirm) return close(true);
      confirm.disabled = true;
      try { const out = await onConfirm(); close(out ?? true); }
      catch (err) { errorBox.hidden = false; errorBox.textContent = err.message || "Error"; confirm.disabled = false; }
    } }, confirmText);
    const overlay = h("div", { class: "overlay", onclick: (e) => { if (e.target === overlay) close(null); } },
      h("div", { class: "modal", role: "dialog", "aria-modal": "true", "aria-label": title },
        h("h2", {}, title), h("div", { class: "modal-body" }, errorBox, body),
        h("div", { class: "modal-foot" }, h("button", { class: "btn", type: "button", onclick: () => close(null) }, "Cancelar"), confirm)));
    document.addEventListener("keydown", onKey);
    document.body.append(overlay);
    overlay.querySelector("textarea, input, select")?.focus();
  });
}

export function debounce(fn, ms = 350) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}
