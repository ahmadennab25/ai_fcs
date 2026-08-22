"""
Standalone demo of the content pipeline flow.

Runs both AI agents end-to-end on a sample campaign topic WITHOUT touching
the database, so you can try the agents before wiring up PostgreSQL.

All output goes through the standard `logging` module (never `print`), so
it plays nicely with the project's logging configuration and shows up the
same way a real failure would.

Usage:
    python run_pipeline.py
"""
import logging
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.flows.content_pipeline.flow import ContentPipelineFlow  # noqa: E402

logger = logging.getLogger(__name__)

SAMPLE_TOPIC = "Launching our new pumpkin spice cold brew for fall"
SAMPLE_CAMPAIGN_OBJECTIVE = (
    "Drive awareness and in-store trial of the new seasonal pumpkin spice "
    "cold brew among young adults during the first two weeks of the fall menu."
)
SAMPLE_TARGET_AUDIENCE = "Coffee lovers aged 18-30 who follow us on Facebook"
SAMPLE_TONE = "playful"
SAMPLE_BRAND_VOICE = (
    "Warm, upbeat and a little cheeky. Short sentences. Uses emoji sparingly "
    "but never uses slang that feels forced."
)
SAMPLE_KEYWORDS = ["#PumpkinSpice", "#ColdBrew", "#FallMenu"]


def main():
    try:
        flow = ContentPipelineFlow()
        result = flow.kickoff(
            topic=SAMPLE_TOPIC,
            campaign_objective=SAMPLE_CAMPAIGN_OBJECTIVE,
            target_audience=SAMPLE_TARGET_AUDIENCE,
            tone=SAMPLE_TONE,
            brand_voice=SAMPLE_BRAND_VOICE,
            keywords=SAMPLE_KEYWORDS,
        )
    except ValueError as exc:
        logger.error("Pipeline failed: %s", exc)
        return

    post = result.get("post", {}) or {}
    image = result.get("image", {}) or {}

    logger.info("=" * 60)
    logger.info("GENERATED FACEBOOK POST")
    logger.info("=" * 60)
    logger.info("Caption:\n%s", post.get("caption"))
    logger.info("Hashtags: %s", post.get("hashtags"))
    logger.info("Call to action: %s", post.get("call_to_action"))
    logger.info("Image prompt: %s", post.get("image_prompt"))

    logger.info("=" * 60)
    logger.info("GENERATED IMAGE")
    logger.info("=" * 60)
    logger.info("Prompt used: %s", image.get("prompt_used"))
    logger.info("Image reference (relative to MEDIA_ROOT): %s", image.get("image_reference"))
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
