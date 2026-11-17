from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import PictureViewSet, ProductViewSet

router = DefaultRouter()
router.register(r"products", ProductViewSet)
router.register(r"pictures", PictureViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
