"""Contenido de demostración (sintético): producto ficticio «Nimbus». No contiene datos reales."""

ARTICLES = [
    (
        "Cómo restablecer tu contraseña",
        True,
        "Si olvidaste tu contraseña, entrá a la pantalla de inicio de sesión y elegí «Olvidé mi contraseña». "
        "Ingresá el email de tu cuenta y te enviaremos un enlace de restablecimiento.\n\n"
        "El enlace vence a los 30 minutos y solo se puede usar una vez. Si venció, pedí uno nuevo. Revisá la "
        "carpeta de spam si no lo ves en tu bandeja de entrada.\n\n"
        "Si no recibís el correo después de 10 minutos, verificá que escribiste bien el email de la cuenta. "
        "Si tu cuenta usa verificación en dos pasos, vas a necesitar también el código de tu autenticador.",
    ),
    (
        "Activar la verificación en dos pasos",
        True,
        "La verificación en dos pasos agrega una capa de seguridad a tu cuenta. Para activarla, andá a "
        "Configuración > Seguridad > Verificación en dos pasos y escaneá el código QR con una aplicación "
        "autenticadora.\n\n"
        "Al activarla se muestran 8 códigos de recuperación. Guardalos en un lugar seguro: cada código se puede "
        "usar una sola vez si perdés acceso a tu autenticador.\n\n"
        "Si perdiste el autenticador y no tenés códigos de recuperación, escribí a soporte. Vamos a verificar "
        "tu identidad antes de desactivar la verificación para que puedas configurarla de nuevo.",
    ),
    (
        "Cambiar de plan o cancelar la suscripción",
        True,
        "Podés cambiar de plan desde Configuración > Facturación > Plan. El cambio a un plan superior se aplica "
        "de inmediato y se cobra la diferencia proporcional. El cambio a un plan inferior se aplica al inicio "
        "del siguiente ciclo de facturación.\n\n"
        "Para cancelar la suscripción, elegí «Cancelar suscripción» en la misma pantalla. No se reembolsa el "
        "ciclo en curso: mantenés el acceso hasta el último día del período ya pagado.\n\n"
        "Si cancelás, tus datos se conservan durante 30 días por si querés reactivar la cuenta.",
    ),
    (
        "Descargar facturas y cambiar datos fiscales",
        True,
        "Tus facturas están en Configuración > Facturación > Historial. Podés descargarlas en formato PDF.\n\n"
        "Para cambiar los datos fiscales (razón social o número de identificación fiscal), editá los datos de "
        "facturación antes del próximo ciclo. Las facturas ya emitidas no se modifican.\n\n"
        "Si necesitás corregir una factura ya emitida, escribí a soporte para que emitamos una nota de crédito "
        "y una factura nueva con los datos correctos.",
    ),
    (
        "Qué hacer si un pago es rechazado",
        True,
        "Un pago puede ser rechazado por fondos insuficientes, tarjeta vencida o bloqueo del banco emisor. "
        "Actualizá el método de pago en Configuración > Facturación > Método de pago.\n\n"
        "Reintentamos el cobro automáticamente a las 48 horas y a los 5 días. Si los tres intentos fallan, la "
        "cuenta pasa a modo solo lectura hasta que se regularice el pago.\n\n"
        "Si ves un cobro duplicado en tu resumen, avisanos con una captura: lo revisamos y, si corresponde, "
        "gestionamos el reembolso.",
    ),
    (
        "Exportar tus datos a CSV",
        True,
        "Para exportar datos, andá a Reportes > Exportar, elegí el rango de fechas y el formato CSV. Te "
        "enviaremos por email un enlace de descarga que vence a las 24 horas.\n\n"
        "Cada exportación admite hasta 50.000 filas. Si necesitás más, dividí la exportación en rangos de "
        "fechas más chicos y descargá cada archivo por separado.",
    ),
    (
        "Invitar usuarios a tu equipo",
        True,
        "Para sumar personas a tu equipo, andá a Configuración > Equipo > Invitar usuario, escribí el email y "
        "elegí un rol: Administrador, Editor o Lector.\n\n"
        "La invitación vence a los 7 días y se puede reenviar. La cantidad de usuarios depende de tu plan: si "
        "llegaste al límite, vas a ver un aviso y tendrás que cambiar a un plan superior para invitar más "
        "personas.",
    ),
    (
        "Conectar tu cuenta de correo para las notificaciones",
        True,
        "Podés enviar las notificaciones desde tu propio servidor de correo. En Configuración > Correo "
        "elegí «SMTP personalizado» e ingresá el servidor, el puerto 587 con cifrado TLS, el usuario y una "
        "contraseña de aplicación (no tu contraseña personal).\n\n"
        "Usá el botón «Probar conexión»: si falla, revisá que el puerto no sea el 25, que suele estar bloqueado "
        "por los proveedores de internet, y que la contraseña de aplicación esté bien copiada.",
    ),
    (
        "Eliminar tu cuenta y tus datos",
        True,
        "Para eliminar tu cuenta, andá a Configuración > Cuenta > Eliminar cuenta. La eliminación es "
        "irreversible, pero tenés 30 días de gracia para arrepentirte iniciando sesión de nuevo.\n\n"
        "Pasado ese plazo se borran tus datos. Los registros de facturación se conservan el tiempo que exige la "
        "ley y no pueden eliminarse antes.",
    ),
    (
        "Horarios y canales de soporte",
        True,
        "El soporte atiende de lunes a viernes de 9 a 18 horas (hora de Argentina). Podés crear tickets en "
        "cualquier momento: los respondemos en el siguiente horario de atención.\n\n"
        "Tiempos de primera respuesta según la prioridad: urgente 2 horas hábiles, alta 4 horas, media 8 horas y "
        "baja 24 horas. Los casos urgentes son los que afectan a todo el equipo o impiden facturar.",
    ),
    (
        "Procedimiento interno: reembolsos",
        False,
        "Los reembolsos solo los aprueba un administrador y únicamente dentro de los primeros 14 días del cobro. "
        "Pedí siempre una captura del resumen de la tarjeta antes de gestionar.\n\n"
        "Un cobro duplicado por reintento automático se reembolsa por completo. La acreditación demora entre 5 "
        "y 10 días hábiles según el banco.",
    ),
]
