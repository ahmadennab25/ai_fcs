"""
Pipeline service.

Resolves a brand/campaign by id or name, runs the full content pipeline
(both agents, via ContentPipelineFlow) for a campaign + topic, and fetches
the latest stored results for a post.
"""
import logging

from core.flows.content_pipeline.flow import ContentPipelineFlow
from core.models import Brand, Campaign, FacebookPost, PostImage

logger = logging.getLogger(__name__)


class PipelineService:
    """Resolves campaigns/brands and drives the end-to-end content pipeline."""

    @staticmethod
    def resolve_brand(brand_id=None, name=None) -> Brand:
        if brand_id is not None:
            try:
                return Brand.objects.get(pk=brand_id)
            except Brand.DoesNotExist as exc:
                raise ValueError(f"Brand with id {brand_id} does not exist.") from exc

        if name:
            try:
                return Brand.objects.get(name=name)
            except Brand.DoesNotExist as exc:
                raise ValueError(f"Brand '{name}' does not exist.") from exc

        raise ValueError("Either brand_id or name must be provided to resolve a brand.")

    @staticmethod
    def resolve_campaign(campaign_id=None, title=None, brand=None) -> Campaign:
        if campaign_id is not None:
            try:
                return Campaign.objects.select_related("brand").get(pk=campaign_id)
            except Campaign.DoesNotExist as exc:
                raise ValueError(
                    f"Campaign with id {campaign_id} does not exist."
                ) from exc

        if title and brand is not None:
            try:
                return Campaign.objects.select_related("brand").get(
                    title=title, brand=brand
                )
            except Campaign.DoesNotExist as exc:
                raise ValueError(
                    f"Campaign '{title}' does not exist for brand '{brand.name}'."
                ) from exc

        raise ValueError("Either campaign_id, or title with a brand, must be provided.")

    @staticmethod
    def run(campaign: Campaign, topic: str) -> dict:
        """Run the full pipeline (Agent 1 + Agent 2) and persist the results."""
        if not topic or not topic.strip():
            raise ValueError("A topic is required to run the pipeline.")

        try:
            flow = ContentPipelineFlow()
            final_output = flow.kickoff(campaign_id=campaign.id, topic=topic)
        except ValueError:
            raise
        except Exception as exc:
            logger.error(
                "Content pipeline failed for campaign %s: %s", campaign.id, exc
            )
            raise ValueError(f"The content pipeline failed: {exc}") from exc

        return final_output

    @staticmethod
    def latest(post: FacebookPost) -> PostImage:
        """Return the most recently generated PostImage for a post, if any."""
        return post.images.order_by("-generated_at").first()
