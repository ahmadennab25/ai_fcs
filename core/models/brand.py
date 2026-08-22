from django.db import models


class Brand(models.Model):
    """A brand/company the social-media team manages content for."""

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    voice_guidelines = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "brands"

    def __str__(self) -> str:
        return self.name
