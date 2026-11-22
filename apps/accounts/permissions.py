from rest_framework.permissions import BasePermission

from .models import Role


class IsAgentOrAdmin(BasePermission):
    message = "Solo agentes y administradores."

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.role in (Role.AGENT, Role.ADMIN))


class IsAdminRole(BasePermission):
    message = "Solo administradores."

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.role == Role.ADMIN)
