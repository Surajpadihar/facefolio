from django.urls import path

from .views import ConsentView, PublicEventView, PublicGalleryView, SelfieSearchView

urlpatterns = [
    path("events/<uuid:token>/", PublicEventView.as_view(), name="public-event"),
    path("events/<uuid:token>/gallery/", PublicGalleryView.as_view(), name="public-gallery"),
    path("events/<uuid:token>/consent/", ConsentView.as_view(), name="public-consent"),
    path("events/<uuid:token>/search/", SelfieSearchView.as_view(), name="public-search"),
]
