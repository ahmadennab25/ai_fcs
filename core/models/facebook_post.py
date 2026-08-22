from django.db import models

from .campaign import Campaign


class FacebookPost(models.Model):
    """
    Structured output produced by the Post Writer Agent (Agent 1).

    Stores the ready-to-publish caption, hashtags, call to action and the
    image prompt handed off to the Image Generation Agent (Agent 2).
    """

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="posts",
    )

    topic = models.CharField(max_length=255)
    caption = models.TextField(blank=True)
    hashtags = models.JSONField(default=list, blank=True)
    call_to_action = models.CharField(max_length=255, blank=True)
    image_prompt = models.TextField(blank=True)

    # Full agent response for debugging / audit
    raw_report = models.JSONField(default=dict, blank=True)

    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "facebook_posts"
        ordering = ["-generated_at"]

    def __str__(self) -> str:
        return f"Post: {self.topic} -> {self.campaign.title}"
