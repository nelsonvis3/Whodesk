from django.conf import settings
from django.db import models


class KnowledgeArticle(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    # is_public=False: solo lo ven y lo usan agentes y administradores.
    is_public = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class RagQuery(models.Model):
    """Registro de cada consulta al asistente: sirve para diagnosticar, medir y calibrar."""

    class Mode(models.TextChoices):
        ASSISTANT = "assistant", "Asistente"
        SUGGEST = "suggest", "Sugerencia de respuesta"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rag_queries")
    ticket = models.ForeignKey(
        "tickets.Ticket", null=True, blank=True, on_delete=models.SET_NULL, related_name="rag_queries"
    )
    mode = models.CharField(max_length=10, choices=Mode.choices)
    question = models.TextField()
    provider = models.CharField(max_length=20, blank=True)
    model = models.CharField(max_length=80, blank=True)
    retrieved = models.JSONField(default=list)
    abstained = models.BooleanField(default=False)
    used_llm = models.BooleanField(default=False)
    answer = models.TextField(blank=True)
    retrieval_ms = models.PositiveIntegerField(default=0)
    generation_ms = models.PositiveIntegerField(default=0)
    feedback = models.SmallIntegerField(null=True, blank=True)  # +1 útil, -1 no útil
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
