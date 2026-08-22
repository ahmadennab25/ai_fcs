from django.urls import path

from core.views.brand_views import BrandCreateAPIView
from core.views.campaign_views import CampaignCreateAPIView
from core.views.facebook_post_views import (
    FacebookPostDetailAPIView,
    FacebookPostWriteAPIView,
)
from core.views.pipeline_views import PipelineRunAPIView
from core.views.post_image_views import (
    PostImageDetailAPIView,
    PostImageGenerateAPIView,
)

urlpatterns = [
    path("brands/", BrandCreateAPIView.as_view(), name="brand-create"),
    path("campaigns/", CampaignCreateAPIView.as_view(), name="campaign-create"),
    path("posts/write/", FacebookPostWriteAPIView.as_view(), name="post-write"),
    path("posts/<int:pk>/", FacebookPostDetailAPIView.as_view(), name="post-detail"),
    path("posts/<int:pk>/image/", PostImageGenerateAPIView.as_view(), name="post-image-generate"),
    path("post-images/<int:pk>/", PostImageDetailAPIView.as_view(), name="post-image-detail"),
    path("pipeline/run/", PipelineRunAPIView.as_view(), name="pipeline-run"),
]
