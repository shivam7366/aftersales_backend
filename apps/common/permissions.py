from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and 
                request.auth and 
                request.auth.get('role') == 'customer'
                ) 
    
class IsServiceProfessional(BasePermission):
    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and 
                request.auth and 
                request.auth.get('role') == 'service_professional'
                )

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and 
                request.auth and 
                request.auth.get('role') == 'admin'
                )

class IsAdminOrCustomer(BasePermission):
    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and 
                request.auth and 
                request.auth.get('role') in ['admin', 'customer']
                )

class IsAdminOrServiceProfessional(BasePermission):
    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and 
                request.auth and 
                request.auth.get('role') in ['admin', 'service_professional']
                )
    
