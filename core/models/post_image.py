from django.db import models

from .facebook_post import FacebookPost


class PostImage(models.Model):
    """
    Structured output produced by the Image Generation Agent (Agent 2).

    Stores the final prompt used and the generated image file, linked back
    to the FacebookPost it illustrates.
    """

    post = models.ForeignKey(
        FacebookPost,
        on_delete=models.CASCADE,
        related_name="images",
    )

    prompt_used = models.TextField()
    image_file = models.ImageField(upload_to="post_images/")
    provider = models.CharField(max_length=50, blank=True)
    model = models.CharField(max_length=100, blank=True)

    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "post_images"
        ordering = ["-generated_at"]

    def __str__(self) -> str:
        return f"Image for post #{self.post_id}"
