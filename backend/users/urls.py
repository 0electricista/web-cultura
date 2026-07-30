from django.urls import path, include
from rest_framework import routers
from .views import UserProfileViewSet, UserRegistrationViewSet, GoogleLoginView

router = routers.DefaultRouter()

# router.register(r'ruta', Controlador, basename='nombre_a_modo_de_variable_para_la_url')
router.register(r'register', UserRegistrationViewSet, basename='user-register')
router.register(r'profile', UserProfileViewSet, basename='user-profile')

urlpatterns = [
    path('', include(router.urls)),
    path('google-login/', GoogleLoginView.as_view(), name='google-login'),
]