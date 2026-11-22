# Whodesk

Sistema de tickets de soporte con asistente de IA, estilo Freshdesk. Un único servicio Django sirve la API REST y el frontend.

**[Demo en vivo](https://TU-APP.onrender.com)** · **[API docs](https://TU-APP.onrender.com/api/docs/)** · [Evaluación del asistente](docs/eval.md)

## Demo

Contraseña `demo1234` para todas las cuentas: `lucia@demo.test` (cliente), `martin@demo.test` (agente), `admin@demo.test` (admin).
Los datos son ficticios; no cargues información real.

## Funcionalidades

- **Roles** (cliente, agente, admin) con login por email: sesión + CSRF para el frontend y JWT para clientes externos.
- **Tickets** con prioridad, categoría, asignación y notas privadas que el cliente no ve.
- **Máquina de estados** con reglas por rol (transición inválida: `409`) y **auditoría** inmutable de cada cambio.
- **Permisos por objeto**: un ticket ajeno responde `404`.
- **Base de conocimiento** y **asistente de IA** con fuentes: widget para clientes y borrador de respuesta para agentes.
- **Frontend responsive** sin build y **API documentada** con OpenAPI.

## Stack

Python 3.12 · Django · Django REST framework · PostgreSQL · HTML/CSS/ES modules · Docker · GitHub Actions · pytest · ruff

## Inicio rápido

```bash
git clone https://github.com/nelsonvis3/whodesk.git && cd whodesk
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver        # http://127.0.0.1:8000
```

Con Docker: `docker compose up --build`

## Asistente de IA

La búsqueda (BM25) corre dentro del servicio, sin descargar modelos. Si el mejor fragmento no supera un umbral, el asistente se abstiene. Las fuentes las arma el código, no el modelo.

| `LLM_PROVIDER` | Comportamiento |
|---|---|
| `none` (default) | Muestra el fragmento más relevante, sin costo. |
| `anthropic` / `openai` | Genera la respuesta por API (requiere `LLM_API_KEY` y `LLM_MODEL`). |

Si el proveedor falla, cae al modo sin LLM. Los clientes solo consultan artículos públicos, y de los tickets se indexa únicamente la nota de resolución.
Evaluación: Hit@1 95 % sobre 30 preguntas propias; es un corpus chico escrito por el mismo autor, ver [`docs/eval.md`](docs/eval.md).

## Despliegue

`render.yaml` define un servicio web y una base PostgreSQL. En Render: *New → Blueprint* y elegir el repositorio. Para activar la IA, cargar `LLM_PROVIDER`, `LLM_API_KEY` y `LLM_MODEL`.
Las variables están en `.env.example`. Con otro proveedor sirve el mismo `Dockerfile` (`DATABASE_URL`, `SECRET_KEY`, `ALLOWED_HOSTS`).

> Las cuentas demo, incluida la de admin, tienen contraseña pública. Usalas solo como sandbox o cambiá `DEMO_PASSWORD`.

## Tests

```bash
pytest --cov=apps
ruff check . && ruff format --check .
python manage.py eval_rag --sweep
```

## Decisiones de diseño

- Reglas de negocio en `services.py`, atómicas (`transaction.atomic` + `select_for_update`); visibilidad por rol en `selectors.py`.
- Sesión + CSRF en el frontend (mismo origen) en lugar de tokens en `localStorage`.
- BM25 en lugar de embeddings: sin dependencias, a costa de no entender paráfrasis.

## Limitaciones

Búsqueda léxica, índice en memoria, sin adjuntos ni emails, y la calidad de la respuesta generada por el LLM no está evaluada.

## Autor

**Nelson Sivisstum** · [Portfolio](https://TU-PORTFOLIO) · [LinkedIn](https://linkedin.com/in/TU-PERFIL)
