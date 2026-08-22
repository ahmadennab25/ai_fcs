from rest_framework import serializers

from core.models import Brand, Campaign, FacebookPost, PostImage


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = [
            "id",
            "name",
            "description",
            "voice_guidelines",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = [
            "id",
            "brand",
            "title",
            "objective",
            "target_audience",
            "tone",
            "keywords",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_keywords(self, value):
        if not isinstance(value, list) or not all(isinstance(k, str) for k in value):
            raise serializers.ValidationError("keywords must be a list of strings.")
        return value


class FacebookPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacebookPost
        fields = [
            "id",
            "campaign",
            "topic",
            "caption",
            "hashtags",
            "call_to_action",
            "image_prompt",
            "raw_report",
            "generated_at",
        ]
        read_only_fields = ["id", "generated_at"]


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = [
            "id",
            "post",
            "prompt_used",
            "image_file",
            "provider",
            "model",
            "generated_at",
        ]
        read_only_fields = ["id", "generated_at"]


class WritePostActionSerializer(serializers.Serializer):
    """Input for FCS-111 — POST /api/posts/write/"""

    campaign_id = serializers.IntegerField()
    topic = serializers.CharField()


class PipelineRunActionSerializer(serializers.Serializer):
    """Input for FCS-115 — POST /api/pipeline/run/"""

    campaign_id = serializers.IntegerField()
    topic = serializers.CharField()
