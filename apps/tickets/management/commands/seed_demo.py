"""Carga datos de demostración sintéticos: usuarios, categorías, artículos y tickets con historial."""

import os
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.knowledge.demo_data import ARTICLES
from apps.knowledge.models import KnowledgeArticle, RagQuery
from apps.tickets import services
from apps.tickets.models import Category, Comment, Ticket, TicketEvent

USERS = [
    ("admin@demo.test", "Ana", "Admin", Role.ADMIN),
    ("martin@demo.test", "Martín", "Gómez", Role.AGENT),
    ("sofia@demo.test", "Sofía", "Ruiz", Role.AGENT),
    ("lucia@demo.test", "Lucía", "Fernández", Role.CUSTOMER),
    ("diego@demo.test", "Diego", "Pérez", Role.CUSTOMER),
    ("carla@demo.test", "Carla", "Benítez", Role.CUSTOMER),
]
CATEGORIES = ["Cuenta y acceso", "Facturación", "Integraciones", "Errores técnicos", "Consultas generales"]

# (cliente, categoría, prioridad, título, descripción, estado final, agente, nota de resolución, [(autor, texto, interno)])
TICKETS = [
    (
        "lucia",
        "Cuenta y acceso",
        "high",
        "No me llega el correo para restablecer mi contraseña",
        "Pedí el enlace de restablecimiento tres veces y no recibo nada, ni en spam. Necesito entrar hoy.",
        "closed",
        "martin",
        "El email de la cuenta tenía una letra de más. Se corrigió y se reenvió el enlace, que vence a los 30 minutos.",
        [
            ("martin", "Hola Lucía, estamos revisando el email asociado a tu cuenta.", False),
            ("martin", "Parece un error de tipeo en el email registrado.", True),
            ("lucia", "¡Ahora sí me llegó, gracias!", False),
        ],
    ),
    (
        "diego",
        "Facturación",
        "high",
        "Veo un cobro duplicado en mi tarjeta",
        "Este mes me cobraron dos veces el plan. Adjunto captura del resumen.",
        "resolved",
        "sofia",
        "Cobro duplicado por reintento automático. Se aprobó el reembolso completo; la acreditación demora de 5 a 10 días hábiles.",
        [
            ("sofia", "Diego, confirmamos el cobro duplicado. Gestionamos el reembolso.", False),
            ("sofia", "Aprobado por admin según el procedimiento interno de reembolsos.", True),
        ],
    ),
    (
        "carla",
        "Errores técnicos",
        "medium",
        "Error al exportar un reporte grande",
        "Cuando exporto todo el año me aparece un error y no llega el archivo.",
        "closed",
        "martin",
        "La exportación superaba el límite de 50.000 filas. Se dividió por trimestres y el enlace de descarga vence a las 24 horas.",
        [
            ("martin", "Probá exportar por trimestres, el límite es de 50.000 filas por archivo.", False),
            ("carla", "Listo, así funcionó.", False),
        ],
    ),
    (
        "lucia",
        "Cuenta y acceso",
        "urgent",
        "Perdí mi autenticador y no puedo entrar",
        "Cambié de teléfono y no tengo los códigos de verificación en dos pasos. No puedo acceder a la cuenta.",
        "resolved",
        "sofia",
        "Se verificó la identidad de la titular por email y se desactivó la verificación en dos pasos para que la configure de nuevo.",
        [
            (
                "sofia",
                "Necesitamos confirmar tu identidad: ¿podés responder desde el email de la cuenta?",
                False,
            ),
            ("lucia", "Ya respondí desde ese email.", False),
        ],
    ),
    (
        "diego",
        "Integraciones",
        "medium",
        "Las notificaciones por correo no salen desde mi servidor",
        "Configuré mi SMTP pero la prueba de conexión falla. Uso el puerto 25.",
        "closed",
        "martin",
        "El puerto 25 estaba bloqueado por el proveedor. Se cambió al 587 con TLS y contraseña de aplicación; la prueba fue exitosa.",
        [
            ("martin", "El puerto 25 suele estar bloqueado, probá con el 587 y TLS.", False),
            ("diego", "Funcionó. Gracias.", False),
        ],
    ),
    (
        "carla",
        "Cuenta y acceso",
        "low",
        "No puedo invitar a un compañero nuevo al equipo",
        "Al intentar invitar a un colega me dice que no se puede. Somos 5 personas.",
        "resolved",
        "sofia",
        "El plan había alcanzado su límite de usuarios. La clienta pasó a un plan superior y la invitación se envió correctamente.",
        [
            (
                "sofia",
                "Tu plan llegó al límite de usuarios. Podés pasar a un plan superior desde Facturación.",
                False,
            )
        ],
    ),
    (
        "lucia",
        "Facturación",
        "medium",
        "Necesito cambiar la razón social de una factura",
        "La factura del mes pasado salió con una razón social vieja. ¿Pueden corregirla?",
        "resolved",
        "martin",
        "Se emitió una nota de crédito y una factura nueva con la razón social correcta. Las facturas emitidas no se modifican.",
        [("martin", "Emitimos una nota de crédito y una factura nueva. Te llegan por email.", False)],
    ),
    (
        "diego",
        "Consultas generales",
        "low",
        "¿Cuál es el horario de atención?",
        "Quiero saber en qué horarios responden los tickets.",
        "closed",
        "sofia",
        "Se informó el horario de atención de lunes a viernes de 9 a 18 horas y los tiempos de primera respuesta.",
        [],
    ),
    (
        "carla",
        "Facturación",
        "high",
        "Mi pago fue rechazado y la cuenta quedó en solo lectura",
        "Cambié de tarjeta pero sigo viendo el aviso de pago rechazado y no puedo editar nada.",
        "in_progress",
        "martin",
        "",
        [("martin", "Estamos verificando el último intento de cobro, ya te cuento.", False)],
    ),
    (
        "lucia",
        "Errores técnicos",
        "medium",
        "La página de reportes carga muy lento",
        "Desde ayer la sección de reportes tarda más de un minuto en abrir.",
        "in_progress",
        "sofia",
        "",
        [("sofia", "¿Podés indicarnos qué navegador usás?", False)],
    ),
    (
        "diego",
        "Cuenta y acceso",
        "medium",
        "Quiero cambiar el email de mi cuenta",
        "Cambié de trabajo y necesito usar otro email para entrar.",
        "waiting_customer",
        "martin",
        "",
        [
            (
                "martin",
                "Para verificar la titularidad, ¿podés confirmar el último dígito de tu tarjeta?",
                False,
            )
        ],
    ),
    (
        "carla",
        "Consultas generales",
        "low",
        "¿Cómo cancelo mi suscripción?",
        "Quiero dar de baja mi plan a fin de mes, no sé dónde hacerlo.",
        "open",
        None,
        "",
        [],
    ),
    (
        "lucia",
        "Integraciones",
        "high",
        "El webhook de pagos dejó de enviar eventos",
        "Desde la madrugada no recibimos los eventos de pago en nuestro sistema.",
        "open",
        None,
        "",
        [],
    ),
    (
        "diego",
        "Errores técnicos",
        "urgent",
        "No puedo iniciar sesión desde ninguna cuenta del equipo",
        "Todo el equipo recibe error al iniciar sesión desde esta mañana. No podemos facturar.",
        "open",
        None,
        "",
        [],
    ),
    (
        "carla",
        "Facturación",
        "medium",
        "Pedido de factura con otros datos fiscales",
        "Necesito la factura del trimestre a nombre de mi empresa nueva.",
        "open",
        None,
        "",
        [],
    ),
    (
        "lucia",
        "Consultas generales",
        "low",
        "¿Pueden eliminar mi cuenta?",
        "Dejé de usar el servicio y quiero eliminar mi cuenta y mis datos.",
        "open",
        None,
        "",
        [],
    ),
]


class Command(BaseCommand):
    help = "Carga datos de demostración (sintéticos). Usá --reset para borrar los existentes."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Borra tickets, artículos y usuarios demo.")

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts["reset"]:
            RagQuery.objects.all().delete()
            Ticket.objects.all().delete()
            KnowledgeArticle.objects.all().delete()
            User.objects.filter(email__endswith="@demo.test").delete()
        elif Ticket.objects.exists() or User.objects.filter(email__endswith="@demo.test").exists():
            self.stdout.write("Ya hay datos de demo. Usá --reset para recrearlos.")
            return

        password = os.environ.get("DEMO_PASSWORD", "demo1234")
        users = {}
        for email, first, last, role in USERS:
            u = User.objects.create_user(email, password, first_name=first, last_name=last, role=role)
            users[email.split("@")[0]] = u
        cats = {n: Category.objects.create(name=n) for n in CATEGORIES}
        for title, public, body in ARTICLES:
            KnowledgeArticle.objects.create(title=title, body=body, is_public=public)

        now = timezone.now()
        for i, (cust, cat, prio, title, desc, final, agent, note, comments) in enumerate(TICKETS):
            customer = users[cust]
            t = services.create_ticket(
                customer, title=title, description=desc, priority=prio, category=cats[cat]
            )
            ag = users.get(agent) if agent else None
            if ag and final != "open":
                services.transition_ticket(ag, t.pk, "in_progress")  # el agente toma el ticket
            for author, text, internal in comments:
                services.add_comment(users[author], t.pk, body=text, internal=internal)
            if ag and final == "waiting_customer":
                services.transition_ticket(ag, t.pk, "waiting_customer")
            if ag and final in ("resolved", "closed"):
                services.transition_ticket(ag, t.pk, "resolved", note)
            if final == "closed":
                services.transition_ticket(customer, t.pk, "closed")
            # Distribuye las fechas en los últimos ~20 días para que la demo se vea natural.
            base = now - timedelta(days=(len(TICKETS) - i) * 1.2, hours=i % 5)
            Ticket.objects.filter(pk=t.pk).update(created_at=base, updated_at=base + timedelta(hours=3))
            for n, e in enumerate(TicketEvent.objects.filter(ticket=t)):
                TicketEvent.objects.filter(pk=e.pk).update(created_at=base + timedelta(minutes=20 * n))
            for n, c in enumerate(Comment.objects.filter(ticket=t)):
                Comment.objects.filter(pk=c.pk).update(created_at=base + timedelta(minutes=35 * (n + 1)))

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo cargada: {len(USERS)} usuarios, {len(ARTICLES)} artículos, {len(TICKETS)} tickets. "
                f"Contraseña de los usuarios demo: {password}"
            )
        )
