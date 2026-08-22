"""FCS-104 — Campaign endpoints."""
import logging

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from core.serializers import CampaignSerializer

logger = logging.getLogger(__name__)


class CampaignCreateAPIView(APIView):
    def post(self, request):
        try:
            serializer = CampaignSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except (ValidationError, ValueError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error("Unexpected error creating campaign: %s", exc)
            return Response(
                {"detail": "An unexpected error occurred while creating the campaign."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
