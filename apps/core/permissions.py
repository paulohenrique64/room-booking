from rest_framework.permissions import BasePermission


class IsOwnerOrStaff(BasePermission):
    """Permite acesso ao dono do objeto ou a usuários staff."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        owner = getattr(obj, 'professor', None) or getattr(obj, 'user', None)
        return owner == request.user
