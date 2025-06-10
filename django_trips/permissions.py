from rest_framework.permissions import BasePermission


class IsStaffForDeleteOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method.lower() == "delete":
            return request.user and request.user.is_staff
        return True
