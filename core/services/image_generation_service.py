"""
Image Generation service.

Runs Agent 2 (Image Generation Crew) on a FacebookPost's image_prompt and
stores the resulting file as a PostImage linked to that post. Fails with a
readable ValueError (never a silent 500) whenever image generation is
unavailable, e.g. no OpenAI API key configured, or offline.
"""
import json
import logging
import os

from django.conf import settings
from django.core.files import File

from core.crews import ImageGenerationCrew
from core.models import FacebookPost, PostImage
from core.utils import parse_json_output

logger = logging.getLogger(__name__)


class ImageGenerationService:
    """Runs the Image Generation Crew and persists its output as a PostImage."""

    @staticmethod
    def run(post: FacebookPost) -> PostImage:
        if not post.image_prompt or not post.image_prompt.strip():
            raise ValueError(
                f"Post #{post.id} has no image_prompt to generate an image from."
            )

        if not settings.OPENAI_API_KEY:
            logger.error(
                "OPENAI_API_KEY is not configured; cannot generate image for post %s.",
                post.id,
            )
            raise ValueError(
                "Image generation is unavailable: OPENAI_API_KEY is not configured."
            )

        inputs = {
            "image_prompt": post.image_prompt,
            "caption": post.caption,
        }

        try:
            result = ImageGenerationCrew().crew().kickoff(inputs=inputs)
        except Exception as exc:
            logger.error(
                "Image Generation Crew failed for post %s: %s", post.id, exc
            )
            raise ValueError(f"Could not generate the image: {exc}") from exc

        try:
            report = parse_json_output(result.raw)
        except json.JSONDecodeError as exc:
            logger.error("Image Generation Crew returned invalid JSON: %s", exc)
            raise ValueError(
                "The image generation agent returned an invalid response."
            ) from exc

        image_reference = report.get("image_reference")
        if not image_reference:
            logger.error(
                "Image Generation Crew returned no image_reference for post %s",
                post.id,
            )
            raise ValueError("The image generation agent did not return an image.")

        absolute_path = os.path.join(settings.MEDIA_ROOT, image_reference)
        if not os.path.exists(absolute_path):
            logger.error("Generated image file not found on disk: %s", absolute_path)
            raise ValueError("The generated image file could not be found.")

        with open(absolute_path, "rb") as image_file:
            post_image = PostImage.objects.create(
                post=post,
                prompt_used=report.get("prompt_used", "") or "",
                provider="openai",
                model=settings.OPENAI_IMAGE_MODEL,
            )
            post_image.image_file.save(
                os.path.basename(absolute_path), File(image_file), save=True
            )

        return post_image
