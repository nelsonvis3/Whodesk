import { post } from "../api.js";
import { h } from "../dom.js";
import { state } from "../state.js";

function brand(className) {
  return h("div", { class: `brand ${className}` }, h("span", { class: "brand-mark", "aria-hidden": "true" }, "?"), "Whodesk");
}

function workflowSketch() {
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", "0 0 760 390");
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-labelledby", "whodesk-sketch-title whodesk-sketch-description");
  const title = document.createElementNS(ns, "title");
  title.id = "whodesk-sketch-title";
  title.textContent = "Whodesk en uso";
  const description = document.createElementNS(ns, "desc");
  description.id = "whodesk-sketch-description";
  description.textContent = "Vista en perspectiva de un ticket con la consulta de una cliente, la respuesta del agente y la persona responsable.";
  svg.append(title, description);

  const add = (parent, tag, attrs = {}) => {
    const node = document.createElementNS(ns, tag);
    for (const [name, value] of Object.entries(attrs)) node.setAttribute(name, value);
    parent.append(node);
    return node;
  };
  const group = (parent, transform) => add(parent, "g", { transform });
  const rect = (parent, x, y, width, height, fill = "#fff", rx = 0, stroke = "#000", strokeWidth = 1.5) =>
    add(parent, "rect", { x, y, width, height, rx, fill, stroke, "stroke-width": strokeWidth });
  const line = (parent, x1, y1, x2, y2, stroke = "#000", strokeWidth = 1) =>
    add(parent, "line", { x1, y1, x2, y2, stroke, "stroke-width": strokeWidth, "stroke-linecap": "round" });
  const label = (parent, x, y, value, { size = 12, fill = "#000", weight = 400 } = {}) => {
    const node = add(parent, "text", { x, y, fill, "font-size": size, "font-weight": weight, "font-family": "system-ui, sans-serif" });
    node.textContent = value;
    return node;
  };

  const screen = group(svg, "matrix(1,.045,-.12,1,94,18)");
  rect(screen, 13, 14, 540, 300, "#000", 12, "#000", 1);
  rect(screen, 0, 0, 540, 300, "#fff", 12, "#000", 2);
  rect(screen, 0, 0, 540, 38, "#fff", 12, "#000", 1.5);
  rect(screen, 0, 27, 540, 11, "#fff", 0, "#fff", 0);
  rect(screen, 14, 10, 20, 20, "#000", 5, "#000", 1);
  label(screen, 20, 25, "?", { size: 15, fill: "#fff", weight: 700 });
  label(screen, 42, 25, "Whodesk", { size: 14, weight: 700 });
  label(screen, 444, 24, "VISTA DEL TICKET", { size: 9, weight: 700 });
  line(screen, 0, 38, 540, 38, "#000", 1.5);

  rect(screen, 0, 39, 104, 261, "#000", 0, "#000", 1);
  label(screen, 16, 65, "ESPACIO", { size: 9, fill: "#fff", weight: 700 });
  rect(screen, 10, 77, 83, 30, "#fff", 5, "#fff", 1);
  label(screen, 22, 97, "Tickets", { size: 12, weight: 700 });
  label(screen, 22, 132, "Base de ayuda", { size: 10, fill: "#fff" });
  line(screen, 12, 153, 91, 153, "#fff", 1);
  label(screen, 16, 177, "Bandeja", { size: 9, fill: "#fff", weight: 700 });
  label(screen, 22, 201, "Sin asignar  4", { size: 10, fill: "#fff" });
  label(screen, 22, 225, "Asignados a mí", { size: 10, fill: "#fff" });

  label(screen, 124, 65, "No puedo iniciar sesión", { size: 16, weight: 700 });
  label(screen, 124, 85, "Ticket #248 · María Sosa", { size: 10 });
  rect(screen, 447, 50, 76, 23, "#000", 11, "#000", 1);
  label(screen, 458, 65, "EN CURSO", { size: 9, fill: "#fff", weight: 700 });

  rect(screen, 120, 98, 264, 66, "#fff", 8, "#000", 1.5);
  label(screen, 132, 117, "María Sosa · Cliente", { size: 10, weight: 700 });
  label(screen, 132, 140, "No puedo entrar desde esta mañana.", { size: 11 });
  rect(screen, 165, 175, 219, 57, "#000", 8, "#000", 1);
  label(screen, 177, 195, "Lucía Méndez · Agente", { size: 10, fill: "#fff", weight: 700 });
  label(screen, 177, 216, "Ya restablecí tu acceso.", { size: 11, fill: "#fff" });
  label(screen, 121, 253, "RESPUESTA ENVIADA · 10:42", { size: 9, weight: 700 });
  line(screen, 120, 266, 384, 266, "#000", 1);

  rect(screen, 400, 87, 125, 172, "#fff", 8, "#000", 1.5);
  label(screen, 412, 108, "RESPONSABLE", { size: 9, weight: 700 });
  line(screen, 412, 118, 513, 118, "#000", 1);
  rect(screen, 412, 130, 22, 22, "#000", 11, "#000", 1);
  label(screen, 420, 145, "L", { size: 11, fill: "#fff", weight: 700 });
  label(screen, 441, 140, "Lucía Méndez", { size: 9, weight: 700 });
  label(screen, 412, 172, "ESTADO", { size: 9, weight: 700 });
  rect(screen, 412, 181, 91, 24, "#fff", 5, "#000", 1);
  label(screen, 421, 197, "En progreso", { size: 10 });
  label(screen, 412, 229, "Actividad registrada", { size: 9 });

  const overlay = group(svg, "matrix(1,.04,-.08,1,566,45)");
  rect(overlay, 0, 0, 140, 58, "#fff", 8, "#000", 2);
  rect(overlay, 11, 12, 22, 22, "#000", 11, "#000", 1);
  label(overlay, 19, 27, "✓", { size: 13, fill: "#fff", weight: 700 });
  label(overlay, 42, 23, "Ticket actualizado", { size: 10, weight: 700 });
  label(overlay, 42, 39, "Historial guardado", { size: 9 });

  return h("figure", { class: "auth-visual" }, svg);
}

function artPanel() {
  return h("section", { class: "auth-art", "aria-label": "Cómo funciona Whodesk" },
    brand("auth-brand"),
    h("div", { class: "auth-intro" },
      h("span", { class: "auth-kicker" }, "SOPORTE, CON CONTEXTO"),
      h("h1", {}, "Del problema a la solución, sin perder el hilo."),
      h("p", {}, "Cada ticket reúne la consulta, a la persona responsable y la respuesta en la misma conversación.")),
    workflowSketch());
}

function authLayout(title, subtitle, form, footer, extra) {
  return h("div", { class: "auth" }, artPanel(),
    h("section", { class: "auth-form", "aria-label": title }, h("div", { class: "auth-card" },
      brand("auth-mobile-brand"), h("h2", {}, title), h("p", {}, subtitle), form, footer, extra)));
}

function field(label, input, hint) {
  return h("div", { class: "field" }, h("label", { for: input.id }, label), input, hint ? h("span", { class: "hint" }, hint) : null);
}

export async function renderLogin(root) {
  document.title = "Whodesk · Ingresar";
  const err = h("div", { class: "error-box", hidden: true, role: "alert" });
  const email = h("input", { id: "email", type: "email", autocomplete: "username", required: true, placeholder: "tu@email.com" });
  const pass = h("input", { id: "password", type: "password", autocomplete: "current-password", required: true });
  const btn = h("button", { class: "btn btn-primary", type: "submit", style: "width:100%;justify-content:center" }, "Ingresar");

  async function submit(e) {
    e?.preventDefault();
    err.hidden = true; btn.disabled = true;
    try { state.user = await post("/auth/login/", { email: email.value, password: pass.value }); location.hash = "#/dashboard"; }
    catch (ex) { err.textContent = ex.message; err.hidden = false; btn.disabled = false; }
  }
  const demo = (emailAddress, password, role, description) => h("button", { class: "demo-option", type: "button",
    "aria-label": `Entrar a la demo como ${role}`,
    onclick: () => { email.value = emailAddress; pass.value = password; submit(); } },
    h("span", { class: "demo-option-copy" }, h("strong", {}, role), h("small", {}, description)),
    h("span", { class: "demo-option-action" }, "Ingresar"));
  const form = h("form", { onsubmit: submit }, err, field("Correo electrónico", email), field("Contraseña", pass), btn);
  const demos = h("div", { class: "demo-box" },
    h("strong", {}, "Probar la demo por perfil"),
    h("p", { class: "t-sub" }, "Cada acceso muestra el sistema con permisos diferentes."),
    h("div", { class: "demo-options" },
      demo("lucia@demo.test", "demo1234", "Cliente", "Crear y consultar solicitudes"),
      demo("martin@demo.test", "demo1234", "Agente", "Asignar y responder tickets"),
      demo("admin@demo.test", "demo1234", "Administrador", "Explorar el perfil administrador")));
  root.append(authLayout("Ingresá a Whodesk", "Usá el correo asociado a tu cuenta para continuar.", form,
    h("p", { class: "t-sub", style: "margin-top:18px" }, "¿No tenés cuenta? ", h("a", { href: "#/register" }, "Registrate")), demos));
}

export async function renderRegister(root) {
  document.title = "Whodesk · Crear cuenta";
  const err = h("div", { class: "error-box", hidden: true, role: "alert" });
  const first = h("input", { id: "first", type: "text", autocomplete: "given-name", required: true });
  const last = h("input", { id: "last", type: "text", autocomplete: "family-name" });
  const email = h("input", { id: "email", type: "email", autocomplete: "email", required: true });
  const pass = h("input", { id: "password", type: "password", autocomplete: "new-password", required: true });
  const btn = h("button", { class: "btn btn-primary", type: "submit", style: "width:100%;justify-content:center" }, "Crear cuenta");
  const form = h("form", { onsubmit: async (e) => {
    e.preventDefault(); err.hidden = true; btn.disabled = true;
    try {
      state.user = await post("/auth/register/", { first_name: first.value, last_name: last.value, email: email.value, password: pass.value });
      location.hash = "#/dashboard";
    } catch (ex) { err.textContent = ex.message; err.hidden = false; btn.disabled = false; }
  } }, err, h("div", { class: "row" }, field("Nombre", first), field("Apellido", last)), field("Email", email),
    field("Contraseña", pass, "Mínimo 8 caracteres; evitá contraseñas comunes."), btn);
  root.append(authLayout("Crear cuenta", "Creá tu cuenta para enviar y seguir solicitudes de soporte.", form,
    h("p", { class: "t-sub", style: "margin-top:16px" }, "¿Ya tenés cuenta? ", h("a", { href: "#/login" }, "Ingresá"))));
}
