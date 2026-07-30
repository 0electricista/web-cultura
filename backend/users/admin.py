from django.contrib import admin
from .models import User

# Registramos los modelos que aparecen en el panel de administracion

admin.site.register(User)