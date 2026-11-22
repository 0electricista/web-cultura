from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permite lectura (GET, HEAD, OPTIONS) a cualquier usuario,
    pero restringe creación, edición y borrado a administradores (is_staff).
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)