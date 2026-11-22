"""Búsqueda BM25 en memoria sobre fragmentos de artículos y tickets resueltos."""

import math
from collections import Counter
from dataclasses import dataclass, field

from django.db.models import Count, Max

from apps.tickets.models import Status, Ticket

from .models import KnowledgeArticle
from .text import chunk_text, tokenize

K1, B = 1.5, 0.75


@dataclass
class Chunk:
    source_type: str  # "article" | "ticket"
    source_id: int
    title: str
    text: str
    chunk_index: int = 0
    tf: Counter = field(default_factory=Counter)
    length: int = 0


@dataclass
class Hit:
    chunk: Chunk
    score: float
    coverage: float


class Index:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.df: Counter = Counter()
        for c in chunks:
            for term in c.tf:
                self.df[term] += 1
        self.n = len(chunks)
        self.avgdl = (sum(c.length for c in chunks) / self.n) if self.n else 0.0

    def idf(self, term: str) -> float:
        n = self.df.get(term, 0)
        return math.log(1 + (self.n - n + 0.5) / (n + 0.5))

    def search(self, query: str, k: int = 4, exclude=None) -> list[Hit]:
        q_terms = set(tokenize(query))
        if not q_terms or not self.n:
            return []
        total_idf = sum(self.idf(t) for t in q_terms)
        hits: list[Hit] = []
        for c in self.chunks:
            if exclude and exclude(c):
                continue
            score, matched = 0.0, 0.0
            for t in q_terms:
                f = c.tf.get(t, 0)
                if not f:
                    continue
                idf = self.idf(t)
                matched += idf
                score += idf * (f * (K1 + 1)) / (f + K1 * (1 - B + B * c.length / self.avgdl))
            if score > 0:
                hits.append(Hit(c, score, matched / total_idf if total_idf else 0.0))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:k]


def _make_chunks(source_type, source_id, title, text) -> list[Chunk]:
    out = []
    for i, piece in enumerate(chunk_text(text)):
        # El título se indexa dos veces: pesa más que el cuerpo.
        tokens = tokenize(title) * 2 + tokenize(piece)
        out.append(Chunk(source_type, source_id, title, piece, i, Counter(tokens), len(tokens)))
    return out


def build_index(audience: str) -> Index:
    """audience="public": solo artículos públicos. "agent": todos los artículos + notas de tickets resueltos.

    De los tickets solo se indexan el título y la nota de resolución (nunca la descripción del cliente).
    """
    chunks: list[Chunk] = []
    arts = KnowledgeArticle.objects.filter(is_active=True)
    if audience == "public":
        arts = arts.filter(is_public=True)
    for a in arts:
        chunks += _make_chunks("article", a.pk, a.title, a.body)
    if audience == "agent":
        done = Ticket.objects.filter(status__in=[Status.RESOLVED, Status.CLOSED]).exclude(resolution_note="")
        for t in done:
            chunks += _make_chunks("ticket", t.pk, f"Ticket #{t.pk}: {t.title}", t.resolution_note)
    return Index(chunks)


_CACHE: dict = {}


def _signature(audience: str):
    a = KnowledgeArticle.objects.filter(is_active=True)
    if audience == "public":
        a = a.filter(is_public=True)
    art = a.aggregate(n=Count("id"), m=Max("updated_at"))
    sig = (audience, art["n"], art["m"])
    if audience == "agent":
        t = Ticket.objects.filter(status__in=[Status.RESOLVED, Status.CLOSED]).exclude(resolution_note="")
        tk = t.aggregate(n=Count("id"), m=Max("updated_at"))
        sig += (tk["n"], tk["m"])
    return sig


def get_index(audience: str) -> Index:
    sig = _signature(audience)
    cached = _CACHE.get(audience)
    if cached and cached[0] == sig:
        return cached[1]
    index = build_index(audience)
    _CACHE[audience] = (sig, index)
    return index


def clear_cache():
    _CACHE.clear()
