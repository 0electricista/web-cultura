from rest_framework import viewsets, mixins, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from django.contrib.auth import get_user_model
from .serializers import UserRegistrationSerializer, UserReadSerializer, GoogleSocialAuthSerializer
from .services import verify_google_token_and_create_user

# Separamos vistas, para poder diferenciar acciones sobre la base de datos

# Para evitar errores de importaciones en circulo, llamamos a la clase User siempre con el siguiente metodo
User = get_user_model()

class UserRegistrationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    # Procesaremos solo peticiones POST (CreateModelMixin)
    queryset = User.objects.all()
    serializer_class=UserRegistrationSerializer
    permission_classes=[AllowAny]

class UserProfileViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    # Procesamos solo peticiones GET (ListModelMixin)
    queryset = User.objects.all()
    serializer_class=UserReadSerializer
    permission_classes=[IsAuthenticated]

    # Redefinimos la ruta. No sera /id, sino /me, para favorecer la seguridad del sitio
    @action(detail=False, methods=['get'])
    def me(self, request):

        # Ruta: GET /api/users/profile/me/
        # Devuelve exclusivamente el perfil del usuario que hace la petición.

        # Obtenemos el usuario directamente del token, no de la URL
        usuario_actual = request.user
        
        # Pasamos el usuario por el serializador para convertirlo a JSON
        serializer = self.get_serializer(usuario_actual)
        
        return Response(serializer.data)

class GoogleLoginView(GenericAPIView):
    """
    Endpoint para autenticar a un usuario mediante Google OAuth2.
    Recibe el token de Google, lo valida y devuelve los tokens JWT de acceso y refresco.
    """
    serializer_class = GoogleSocialAuthSerializer    
    permission_classes = [AllowAny]
    # Redefinimos el metodo post
    def post(self, request, *args, **kwargs):
        # 1. Pasamos los datos que llegan (el JSON del frontend) al Serializer
        serializer = self.get_serializer(data=request.data)
        
        # 2. raise_exception=True hace que si falta el 'token', 
        # DRF devuelva automáticamente un error HTTP 400 Bad Request.
        serializer.is_valid(raise_exception=True)
        
        # 3. Extraemos el token de Google ya limpio y validado
        google_token = serializer.validated_data['token']
        
        try:
            # Ejecutamos el servicio
            jwt_tokens = verify_google_token_and_create_user(google_token)
            
            # Devolvemos los tokens al Frontend
            return Response(jwt_tokens, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)