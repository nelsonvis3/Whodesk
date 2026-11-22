from django.contrib import admin

from .models import KnowledgeArticle, RagQuery


@admin.register(KnowledgeArticle)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "is_public", "is_active", "updated_at")
    list_filter = ("is_public", "is_active")
    search_fields = ("title", "body")


@admin.register(RagQuery)
class RagQueryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "mode",
        "abstained",
        "used_llm",
        "feedback",
        "retrieval_ms",
        "generation_ms",
        "created_at",
    )
    list_filter = ("mode", "abstained", "used_llm", "feedback")
