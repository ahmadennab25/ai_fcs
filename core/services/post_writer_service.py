"""
Post Writer service.

Runs Agent 1 (Post Writer Crew) for a campaign + topic and stores the
result as a FacebookPost. Used directly by the API view — the flow uses
the crew the same way for the full-pipeline path.
"""
import json
import logging

from core.crews import PostWriterCrew
from core.models import Campaign, FacebookPost
from core.utils import parse_json_output

logger = logging.getLogger(__name__)


class PostWriterService:
    """Runs the Post Writer Crew and persists its output as a FacebookPost."""

    @staticmethod
    def run(campaign: Campaign, topic: str) -> FacebookPost:
        if not topic or not topic.strip():
            raise ValueError("A topic is required to write a post.")

        inputs = {
            "topic": topic,
            "campaign_objective": campaign.objective,
            "target_audience": campaign.target_audience,
            "tone": campaign.tone,
            "brand_voice": campaign.brand.voice_guidelines,
            "keywords": ", ".join(campaign.keywords or []),
        }

        try:
            result = PostWriterCrew().crew().kickoff(inputs=inputs)
        except Exception as exc:
            logger.error(
                "Post Writer Crew failed for campaign %s: %s", campaign.id, exc
            )
            raise ValueError(f"Could not generate the post: {exc}") from exc

        try:
            report = parse_json_output(result.raw)
        except json.JSONDecodeError as exc:
            logger.error("Post Writer Crew returned invalid JSON: %s", exc)
            raise ValueError(
                "The post writer agent returned an invalid response."
            ) from exc

        post = FacebookPost.objects.create(
            campaign=campaign,
            topic=topic,
            caption=report.get("caption", "") or "",
            hashtags=report.get("hashtags", []) or [],
            call_to_action=report.get("call_to_action", "") or "",
            image_prompt=report.get("image_prompt", "") or "",
            raw_report=report,
        )
        return post
