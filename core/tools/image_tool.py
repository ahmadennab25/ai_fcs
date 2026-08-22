"""
Image generation tool used by the Art Director agent (Agent 2).

Calls the OpenAI Images API directly and saves the resulting image under
MEDIA_ROOT, returning a relative path the service layer can attach to a
PostImage.image_file. Fails loudly with a readable ValueError (and a
logged error) whenever the API key is missing or the request fails, so the
caller gets a clean 400/500 instead of a silent crash.
"""
import base64
import logging
import os
import uuid
from typing import Type

from crewai.tools import BaseTool
from django.conf import settings
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ImageGenerationToolInput(BaseModel):
    prompt: str = Field(
        ..., description="The final, vivid image prompt to render for Facebook."
    )


class ImageGenerationTool(BaseTool):
    name: str = "generate_facebook_image"
    description: str = (
        "Generates an image from a text prompt using the OpenAI Images API "
        "and returns the relative media path of the saved image file. "
        "Always call this tool to actually produce the image asset."
    )
    args_schema: Type[BaseModel] = ImageGenerationToolInput

    def _run(self, prompt: str) -> str:
        if not prompt or not prompt.strip():
            logger.error("ImageGenerationTool called with an empty prompt.")
            raise ValueError("An image prompt is required to generate an image.")

        if not settings.OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY is not configured; cannot generate image.")
            raise ValueError(
                "Image generation is unavailable: OPENAI_API_KEY is not configured."
            )

        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.images.generate(
                model=settings.OPENAI_IMAGE_MODEL,
                prompt=prompt,
                size="1024x1024",
                n=1,
            )
        except Exception as exc:
            logger.error("OpenAI image generation request failed: %s", exc)
            raise ValueError(f"Image generation failed: {exc}") from exc

        try:
            image_bytes = self._extract_image_bytes(response)
        except Exception as exc:
            logger.error("Failed to read image data from OpenAI response: %s", exc)
            raise ValueError(f"Could not read generated image data: {exc}") from exc

        try:
            relative_path = self._save_to_media(image_bytes)
        except OSError as exc:
            logger.error("Failed to save generated image to media directory: %s", exc)
            raise ValueError(f"Could not save the generated image: {exc}") from exc

        return relative_path

    @staticmethod
    def _extract_image_bytes(response) -> bytes:
        item = response.data[0]
        image_b64 = getattr(item, "b64_json", None)
        if image_b64:
            return base64.b64decode(image_b64)

        image_url = getattr(item, "url", None)
        if not image_url:
            raise ValueError("OpenAI response contained neither b64_json nor a url.")

        import requests

        api_response = requests.get(image_url, timeout=30)
        api_response.raise_for_status()
        return api_response.content

    @staticmethod
    def _save_to_media(image_bytes: bytes) -> str:
        folder = "post_images"
        filename = f"{uuid.uuid4().hex}.png"
        relative_path = os.path.join(folder, filename)
        absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        os.makedirs(os.path.dirname(absolute_path), exist_ok=True)

        with open(absolute_path, "wb") as image_file:
            image_file.write(image_bytes)

        return relative_path
