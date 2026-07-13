from django.contrib.auth.mixins import AccessMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


class AdminRoleRequired(AccessMixin):
    
    @method_decorator(csrf_exempt, name='dispatch')
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not request.user.role in ('admin', 'supervisor'):
            return self.handle_no_permission()
        
        return super().dispatch(request, *args, **kwargs)


class CSRFExempt(AccessMixin):
    
    @method_decorator(csrf_exempt, name='dispatch')
    def dispatch(self, request, *args, **kwargs):
        
        return super().dispatch(request, *args, **kwargs)
