from rest_framework import serializers
from django.contrib.auth import get_user_model

# Para evitar errores de importaciones en circulo, llamamos a la clase User siempre con el siguiente metodo
User = get_user_model()

# Creamos 2 serializer, uno para registro y otro para lectura
# Con otros modelos no seria necesario, pero asi dividimos y gestionamos mejor el aislamiento de las contraseñas
class UserRegistrationSerializer(serializers.ModelSerializer):
    # Definimos el modelo que referencia y los campos que entrarian desde la peticion POST
    class Meta:
        model = User
        fields = [
            "email", 
            "password", 
            "full_name"
        ]

        # Definimos configuraciones ajustadas a cada atributo
        extra_kwargs = {
            "password": {"write_only": True, "style": {"input_type": "password"}},
            "full_name": {"required": True}
        }

    # Este metodo create crea el usuario en la base de datos
    # Sobreescribimos el metodo llamando a nuestro metodo definido en el modelo, asi garantizamos la seguridad
    # de la contraseña gracias al metodo set_password
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            full_name=validated_data["full_name"],
        )
        return user
    
class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "is_staff"  # Facilitaria redireccion al panel de administracion en el frontend
        ]

        # Seguro de solo lectura de los atributos del UserReadSerializer

        read_only_fields = fields

# Serializer para la recepcion del token de autenticacion de google
class GoogleSocialAuthSerializer(serializers.Serializer):
    # Solo valida el campo token
    token = serializers.CharField(required = True)