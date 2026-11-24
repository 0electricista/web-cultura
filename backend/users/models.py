import uuid
from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.utils import timezone

# Clase administradora de usuarios (redefinimos metodos create_user y create_superuser)
class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password= None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        
        # Si password es None (Google OAuth), Django lo convierte en unusable_password
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True")

        return self._create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    google_id = models.CharField(max_length=255, blank=True, null=True, unique=True)


    # La variable objects (por convencion se llama asi) define la clase que administra el usuario.
    # Al definir nuestra propia clase UserManager, podemos establecer nuestra logica de negocio sobre los usuarios.
    objects = UserManager()

    # Los usuarios se veran identificados por su email, no por su username (igual para el inicio de sesion)
    USERNAME_FIELD = "email"
    # Campos que son obligatorios al crear un superusuario o al crear un usuario desde el manager.
    REQUIRED_FIELDS = ["full_name"]

    # La clase meta sirve para aplicar restricciones de los modelos en la base de datos.
    # En este caso verbose_name y verbose_name_plural reescriben el nombre (que django da automatico) 
    # de las tablas, tanto en singular como plural 
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return str(self.email or self.full_name or self.id)