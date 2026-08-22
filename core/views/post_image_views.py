"""FCS-112 / FCS-106 — Generate (Agent 2) and view post images."""
import logging

from django.http import Http404
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import FacebookPost, PostImage
from core.serializers import PostImageSerializer
from core.services import ImageGenerationService

logger = logging.getLogger(__name__)


class PostImageGenerateAPIView(APIView):
    """POST /api/posts/<pk>/image/ — generates an image for post <pk>."""

    def post(self, request, pk):
        try:
            post = get_object_or_404(FacebookPost, pk=pk)
            post_image = ImageGenerationService.run(post)

            return Response(
                PostImageSerializer(post_image).data,
                status=status.HTTP_201_CREATED,
            )
        except Http404:
            return Response(
                {"detail": f"Facebook post with id {pk} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error("Unexpected error generating image for post %s: %s", pk, exc)
            return Response(
                {"detail": "An unexpected error occurred while generating the image."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PostImageDetailAPIView(APIView):
    """GET /api/post-images/<pk>/"""

    def get(self, request, pk):
        try:
            post_image = get_object_or_404(PostImage, pk=pk)
            serializer = PostImageSerializer(post_image)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Http404:
            return Response(
                {"detail": "Post image not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as exc:
            logger.error("Unexpected error fetching post image %s: %s", pk, exc)
            return Response(
                {"detail": "An unexpected error occurred while fetching the image."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
