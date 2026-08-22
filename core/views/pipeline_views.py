"""FCS-115 (optional) — run the full pipeline (Agent 1 + Agent 2) in one call."""
import logging

from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Campaign
from core.serializers import PipelineRunActionSerializer
from core.services import PipelineService

logger = logging.getLogger(__name__)


class PipelineRunAPIView(APIView):
    """POST /api/pipeline/run/ — {"campaign_id": int, "topic": str}"""

    def post(self, request):
        try:
            action_serializer = PipelineRunActionSerializer(data=request.data)
            action_serializer.is_valid(raise_exception=True)
            campaign_id = action_serializer.validated_data["campaign_id"]
            topic = action_serializer.validated_data["topic"]

            campaign = get_object_or_404(Campaign, pk=campaign_id)
            final_output = PipelineService.run(campaign, topic)

            return Response(final_output, status=status.HTTP_201_CREATED)
        except Http404:
            return Response(
                {"detail": f"Campaign with id {request.data.get('campaign_id')} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except (ValidationError, ValueError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error("Unexpected error running pipeline: %s", exc)
            return Response(
                {"detail": "An unexpected error occurred while running the pipeline."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
