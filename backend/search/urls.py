from django.urls import path

from .views import (
    BulkDownloadView,
    ConsentView,
    PhotoDownloadView,
    PublicEventView,
    PublicGalleryView,
    SelfieSearchView,
)

urlpatterns = [
    path("events/<uuid:token>/", PublicEventView.as_view(), name="public-event"),
    path("events/<uuid:token>/gallery/", PublicGalleryView.as_view(), name="public-gallery"),
    path("events/<uuid:token>/consent/", ConsentView.as_view(), name="public-consent"),
    path("events/<uuid:token>/search/", SelfieSearchView.as_view(), name="public-search"),
    path("events/<uuid:token>/photos/<int:photo_id>/download/", PhotoDownloadView.as_view(), name="public-download"),
    path("events/<uuid:token>/download-zip/", BulkDownloadView.as_view(), name="public-download-zip"),
]
