from rest_framework.routers import DefaultRouter
from .views import VideoViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'videos', VideoViewSet)

urlpatterns = [
    # other urls
    path("api/", include(router.urls)),
]