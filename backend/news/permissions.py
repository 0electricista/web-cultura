from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrAdminOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        # Métodos de lectura son siempre públicos
        if request.method in SAFE_METHODS:
            return True
        # Para cualquier otra operación, el usuario debe estar autenticado
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Lectura siempre permitida
        if request.method in SAFE_METHODS:
            return True
        # Solo el dueño o un admin pueden modificar/borrar
        return obj.user == request.user or request.user.is_staff
