"""
Content pipeline flow.

Orchestrates the two AI agents in sequence:

    1. Post Writer Agent      -> writes the Facebook post + an image prompt.
    2. Image Generation Agent -> renders that image prompt into an image.

The flow runs in one of two modes:

* **Database mode** (used by the API): the caller passes only
  ``campaign_id`` and ``topic``. The flow loads the campaign and its brand
  from the database. When ``persist`` is true it also writes a
  ``FacebookPost`` and a ``PostImage`` back to the database.

* **Raw mode** (used by ``run_pipeline.py`` for a quick no-database demo):
  the caller passes the campaign fields directly.

All database access happens in the synchronous ``kickoff`` wrapper — before
and after the async crew steps run — so Django's ORM is never touched from
inside the flow's async event loop.
"""
import json
import logging
import os

from crewai.flow import Flow, listen, start

from core.crews import ImageGenerationCrew, PostWriterCrew
from core.models import Campaign, FacebookPost, PostImage
from core.utils import parse_json_output

from .schema import ContentPipelineState

logger = logging.getLogger(__name__)


class ContentPipelineFlow(Flow[ContentPipelineState]):

    # ------------------------------------------------------------------
    # Async crew steps — these only touch the state, never the database.
    # ------------------------------------------------------------------
    @start()
    async def write_post(self):
        """Step 1: run the Post Writer Agent."""
        result = await (
            PostWriterCrew()
            .crew()
            .kickoff_async(
                inputs={
                    "topic": self.state.topic,
                    "campaign_objective": self.state.campaign_objective,
                    "target_audience": self.state.target_audience,
                    "tone": self.state.tone,
                    "brand_voice": self.state.brand_voice,
                    "keywords": ", ".join(self.state.keywords or []),
                }
            )
        )
        try:
            self.state.post_output = parse_json_output(result.raw)
        except json.JSONDecodeError as exc:
            logger.error("Post writer JSON decode error: %s", exc)
            self.state.post_output = {
                "error": "Invalid JSON returned by the post writer agent"
            }
        return self.state.post_output

    @listen(write_post)
    async def generate_image(self):
        """Step 2: run the Image Generation Agent on step 1's image prompt."""
        image_prompt = (self.state.post_output or {}).get("image_prompt", "")
        caption = (self.state.post_output or {}).get("caption", "")

        result = await (
            ImageGenerationCrew()
            .crew()
            .kickoff_async(
                inputs={
                    "image_prompt": image_prompt,
                    "caption": caption,
                }
            )
        )
        try:
            self.state.image_output = parse_json_output(result.raw)
        except json.JSONDecodeError as exc:
            logger.error("Image generation JSON decode error: %s", exc)
            self.state.image_output = {
                "error": "Invalid JSON returned by the image generation agent"
            }
        return self.state.image_output

    @listen(generate_image)
    def combine_results(self):
        """Step 3: assemble the final combined result."""
        self.state.final_output = {
            "post": self.state.post_output,
            "image": self.state.image_output,
        }
        return self.state.final_output

    # ------------------------------------------------------------------
    # Database helpers — called only from the synchronous kickoff wrapper.
    # ------------------------------------------------------------------
    @staticmethod
    def _load_campaign_from_db(campaign_id) -> Campaign:
        """Load the campaign (with its brand) for the given id."""
        try:
            return Campaign.objects.select_related("brand").get(pk=campaign_id)
        except Campaign.DoesNotExist as exc:
            logger.error("Campaign %s does not exist: %s", campaign_id, exc)
            raise ValueError(f"Campaign with id {campaign_id} does not exist.") from exc

    def _persist_results(self, campaign: Campaign, topic: str):
        """Write the generated post and image to the database."""
        from django.conf import settings
        from django.core.files import File

        report = self.state.post_output or {}

        post = FacebookPost.objects.create(
            campaign=campaign,
            topic=topic,
            caption=report.get("caption", "") or "",
            hashtags=report.get("hashtags", []) or [],
            call_to_action=report.get("call_to_action", "") or "",
            image_prompt=report.get("image_prompt", "") or "",
            raw_report=report,
        )

        image_report = self.state.image_output or {}
        image_reference = image_report.get("image_reference")
        post_image = None

        if image_reference:
            absolute_path = os.path.join(settings.MEDIA_ROOT, image_reference)
            if os.path.exists(absolute_path):
                with open(absolute_path, "rb") as image_file:
                    post_image = PostImage.objects.create(
                        post=post,
                        prompt_used=image_report.get("prompt_used", "") or "",
                        provider="openai",
                        model=settings.OPENAI_IMAGE_MODEL,
                    )
                    post_image.image_file.save(
                        os.path.basename(absolute_path), File(image_file), save=True
                    )
            else:
                logger.error(
                    "Generated image file not found on disk: %s", absolute_path
                )

        return post, post_image

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def kickoff(
        self,
        campaign_id=None,
        topic=None,
        *,
        campaign_objective="",
        target_audience="",
        tone="",
        brand_voice="",
        keywords=None,
        persist=None,
    ):
        """
        Run the pipeline.

        Database mode (values are read from the DB — the caller only
        supplies a campaign id and a topic):
            flow.kickoff(campaign_id=1, topic="Fall pumpkin latte launch")

        Raw mode (no database — used by the demo script):
            flow.kickoff(
                topic="...",
                campaign_objective="...",
                target_audience="...",
                tone="...",
                brand_voice="...",
                keywords=["..."],
            )

        Returns the combined ``final_output`` dict. When ``persist`` is true
        (the default in database mode) a ``FacebookPost`` and a
        ``PostImage`` row are also created.
        """
        campaign = None

        if campaign_id is not None and topic is not None:
            # ---- Database mode: pull the campaign/brand from the DB ----
            campaign = self._load_campaign_from_db(campaign_id)
            self.state.campaign_id = campaign.id
            self.state.topic = topic
            self.state.campaign_objective = campaign.objective
            self.state.target_audience = campaign.target_audience
            self.state.tone = campaign.tone
            self.state.brand_voice = campaign.brand.voice_guidelines
            self.state.keywords = campaign.keywords or []
            if persist is None:
                persist = True
        else:
            # ---- Raw mode: use whatever the caller passed in ----
            self.state.topic = topic or ""
            self.state.campaign_objective = campaign_objective
            self.state.target_audience = target_audience
            self.state.tone = tone
            self.state.brand_voice = brand_voice
            self.state.keywords = keywords or []
            persist = False

        # Run the async crew steps (no DB access happens inside these).
        super().kickoff()

        if persist and campaign is not None:
            self._persist_results(campaign, topic)

        return self.state.final_output
