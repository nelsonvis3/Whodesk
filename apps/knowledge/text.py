"""Procesamiento de texto en español para la búsqueda léxica (sin dependencias externas).

El stemming es deliberadamente simple (recorta sufijos frecuentes): alcanza para una base de
conocimiento chica y es fácil de explicar, pero no entiende sinónimos ni contexto. Ver docs/eval.md.
"""

import re
import unicodedata

STOPWORDS = set(
    """
a al algo algun alguna algunas alguno algunos ante antes aqui asi aun aunque cada como con contra
cual cuales cuando de del desde donde dos el ella ellas ello ellos en entre era eran es esa esas ese
eso esos esta estaba estan estar este esto estos fue fueron ha han hay hasta he la las le les lo los
mas me mi mis mucho muy nada ni no nos nuestro o os otra otras otro otros para pero poco por porque
que quien quienes se sea ser si sido sin sobre sus su tambien tan tanto te tengo tiene tienen todo
todos tu tus un una unas uno unos y ya yo quiero puedo necesito ayuda hola gracias favor buen buenas
buenos dias tardes noches
""".split()
)

# Sinónimos de dominio: se aplican antes del stemming.
SYNONYMS = {
    "clave": "contrasena",
    "password": "contrasena",
    "pass": "contrasena",
    "passwd": "contrasena",
    "cobro": "pago",
    "cobran": "pago",
    "cobraron": "pago",
    "tarjeta": "pago",
    "debito": "pago",
    "boleta": "factura",
    "comprobante": "factura",
    "recibo": "factura",
    "baja": "eliminar",
    "borrar": "eliminar",
    "cancelar": "eliminar",
    "2fa": "verificacion",
    "autenticador": "verificacion",
    "excel": "csv",
    "planilla": "csv",
    "membresia": "plan",
    "suscripcion": "plan",
    "abono": "plan",
}

_SUFFIXES = (
    "amientos",
    "imientos",
    "amiento",
    "imiento",
    "aciones",
    "uciones",
    "acion",
    "ucion",
    "idades",
    "idad",
    "mente",
    "adores",
    "ador",
    "ables",
    "able",
    "ibles",
    "ible",
    "ando",
    "iendo",
    "aron",
    "ieron",
    "ados",
    "adas",
    "idos",
    "idas",
    "ado",
    "ada",
    "ido",
    "ida",
    "ar",
    "er",
    "ir",
    "es",
    "os",
    "as",
    "s",
)


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def stem(token: str) -> str:
    token = SYNONYMS.get(token, token)
    if len(token) <= 4:
        return token
    for suf in _SUFFIXES:
        if token.endswith(suf) and len(token) - len(suf) >= 3:
            token = token[: -len(suf)]
            break
    if len(token) > 4 and token[-1] in "aeo":
        token = token[:-1]
    return token


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", strip_accents(text.lower()))
    return [stem(w) for w in words if len(w) > 1 and w not in STOPWORDS]


def chunk_text(text: str, max_chars: int = 600) -> list[str]:
    """Divide por párrafos y acumula hasta max_chars. Un párrafo largo se corta por oraciones."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    pieces: list[str] = []
    for p in paras:
        if len(p) <= max_chars:
            pieces.append(p)
            continue
        buf = ""
        for sent in re.split(r"(?<=[.!?])\s+", p):
            if buf and len(buf) + len(sent) + 1 > max_chars:
                pieces.append(buf)
                buf = sent
            else:
                buf = f"{buf} {sent}".strip()
        if buf:
            pieces.append(buf)
    chunks: list[str] = []
    buf = ""
    for piece in pieces:
        if buf and len(buf) + len(piece) + 2 > max_chars:
            chunks.append(buf)
            buf = piece
        else:
            buf = f"{buf}\n\n{piece}".strip()
    if buf:
        chunks.append(buf)
    return chunks
