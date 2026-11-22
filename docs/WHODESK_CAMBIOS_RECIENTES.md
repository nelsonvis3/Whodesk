# Whodesk · cambios recientes

Resumen de los ajustes de interfaz incorporados el 22 de noviembre de 2026.

- **Identidad:** el nombre visible pasó a Whodesk; el logotipo usa un signo de pregunta tipográfico visible y el favicon conserva el signo en blanco sobre negro.
- **Estilo:** la interfaz usa solo negro `#000` y blanco `#fff`. La única excepción de color es la estrella multicolor del botón flotante del asistente de IA.
- **Acceso:** se retiró el listado genérico de estados y se reemplazó la presentación por una maqueta superpuesta en perspectiva, con ticket, conversación y responsable visibles.
- **Conversación:** cada mensaje público y la consulta inicial tienen un botón «Responder a…» debajo. Al elegirlo, el editor indica la persona, el identificador del mensaje y un extracto. La respuesta guarda esa referencia y una cita breve al comienzo del texto para que siga identificable en el historial.
- **Asistente:** volvió a ser una burbuja circular fija en la esquina inferior derecha, con una estrella multicolor inspirada en Gemini y nombre accesible para lectores de pantalla.
- **Cierre:** al cerrar un ticket, aparece «Ticket cerrado» centrado en la parte inferior.

## Alcance

Los cambios de conversación son de frontend. La API actual no relaciona comentarios con un campo `in_reply_to`; por eso la respuesta conserva la referencia como texto en el mensaje, sin crear hilos separados ni cambiar el esquema de datos.
