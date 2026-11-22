from rest_framework import serializers

from .models import KnowledgeArticle


class ArticleListSerializer(serializers.ModelSerializer):
    excerpt = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeArticle
        fields = ["id", "title", "excerpt", "is_public", "is_active", "updated_at"]
        read_only_fields = fields

    def get_excerpt(self, obj) -> str:
        text = obj.body.replace("\n", " ").strip()
        return text[:160] + ("…" if len(text) > 160 else "")


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeArticle
        fields = ["id", "title", "body", "is_public", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class QuestionSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=4000)


class FeedbackSerializer(serializers.Serializer):
    value = serializers.IntegerField()
