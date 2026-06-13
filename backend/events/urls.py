from rest_framework.routers import DefaultRouter

from photos.views import PhotoViewSet

from .views import EventViewSet

router = DefaultRouter()
router.register(r"events", EventViewSet, basename="event")
router.register(r"photos", PhotoViewSet, basename="photo")

urlpatterns = router.urls
