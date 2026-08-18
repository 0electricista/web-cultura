from rest_framework.routers import DefaultRouter
from .views import RentViewSet

router = DefaultRouter()
router.register(r'rents', RentViewSet, basename='rent')

urlpatterns = router.urls