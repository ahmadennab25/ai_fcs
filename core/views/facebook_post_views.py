"""FCS-111 / FCS-105 — Write (Agent 1) and view Facebook posts."""
import logging

from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Campaign, FacebookPost
from core.serializers import FacebookPostSerializer, WritePostActionSerializer
from core.services import PostWriterService

logger = logging.getLogger(__name__)


class FacebookPostWriteAPIView(APIView):
    """POST /api/posts/write/ — {"campaign_id": int, "topic": str}"""

    def post(self, request):
        try:
            action_serializer = WritePostActionSerializer(data=request.data)
            action_serializer.is_valid(raise_exception=True)
            campaign_id = action_serializer.validated_data["campaign_id"]
            topic = action_serializer.validated_data["topic"]

            campaign = get_object_or_404(Campaign, pk=campaign_id)
            post = PostWriterService.run(campaign, topic)

            return Response(
                FacebookPostSerializer(post).data,
                status=status.HTTP_201_CREATED,
            )
        except Http404:
            return Response(
                {"detail": f"Campaign with id {request.data.get('campaign_id')} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except (ValidationError, ValueError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error("Unexpected error writing post: %s", exc)
            return Response(
                {"detail": "An unexpected error occurred while writing the post."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FacebookPostDetailAPIView(APIView):
    """GET /api/posts/<pk>/"""

    def get(self, request, pk):
        try:
            post = get_object_or_404(FacebookPost, pk=pk)
            serializer = FacebookPostSerializer(post)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Http404:
            return Response(
                {"detail": "Facebook post not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as exc:
            logger.error("Unexpected error fetching post %s: %s", pk, exc)
            return Response(
                {"detail": "An unexpected error occurred while fetching the post."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
