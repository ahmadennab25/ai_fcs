from django.db import models

from .brand import Brand


class Campaign(models.Model):
    """The context an AI agent writes Facebook content for."""

    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name="campaigns",
    )
    title = models.CharField(max_length=255)
    objective = models.TextField()
    target_audience = models.CharField(max_length=255)
    tone = models.CharField(max_length=50)
    keywords = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "campaigns"

    def __str__(self) -> str:
        return f"{self.title} ({self.brand.name})"
