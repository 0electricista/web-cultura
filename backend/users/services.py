from typing import Dict
from google.oauth2 import id_token
from google.auth.transport import requests
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

# Para evitar errores de importaciones en circulo, llamamos a la clase User siempre con el siguiente metodo
User = get_user_model()

def verify_google_token_and_create_user(token: str) -> Dict[str, str]:
   
    # Verifica el token JWT proporcionado por Google.
    # Si es válido, obtiene o crea al usuario y genera los tokens de sesión de nuestra API.

    try:
        # 1. Llamada a Google: Verificamos criptográficamente que el token es auténtico
        idinfo = id_token.verify_oauth2_token(token, requests.Request())

        # 2. Extraemos los datos que nos da Google
        email = idinfo['email']
        google_id = idinfo['sub']  # 'sub' es el identificador único e inmutable en Google
        full_name = idinfo.get('name', '')

        # 3. Buscamos al usuario por email, si no existe lo creamos
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'google_id': google_id,
                'full_name': full_name,
            }
        )

        # 4. Ajustes si el usuario es nuevo o si ya existía pero no tenía Google ID
        if created:
            # Como vimos, bloqueamos el acceso por contraseña tradicional
            user.set_unusable_password()
            user.save()
        elif not user.google_id:
            # Si el usuario ya se había registrado antes con contraseña, 
            # vinculamos su cuenta de Google ahora.
            user.google_id = google_id
            user.save()

        # 5. Generamos nuestros propios tokens JWT (El "Pasaporte" de nuestro e-commerce)
        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    except ValueError:
        # Si la firma del token no coincide o ha caducado, id_token lanza un ValueError
        raise ValueError("El token de Google proporcionado es inválido o ha expirado.")