from datetime import datetime, timedelta

from django.utils import timezone
from django.views.generic import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin

from account.models import User
from account.security import (
    AdminRoleRequired,
    CSRFExempt
)
from account.utils import generate_password


class RegisterViewAPI(View):

    @method_decorator(csrf_exempt, name='dispatch')
    def dispatch(self, req, **kwargs):
        return super().dispatch(req, **kwargs)
    
    def post(self, req, *args, **kwargs):

        username = req.POST.get('username', '').strip().lower()
        password = req.POST.get('password', '').strip()
        fullname = req.POST.get('fullname', '')
        password_repeat = req.POST.get('password_repeat')

        errors = []

        if len(password) < 8:
            errors.append('password')
        
        if password != password_repeat:
            errors.append('password-repeat')

        if not 2 < len(fullname) < 50:
            errors.append('fullname')
        
        if not 2 < len(username) < 30 or User.objects.filter(username=username).first():
            errors.append('username')

        if errors:
            return JsonResponse({'errors': errors}, safe=False)
        else:
            user = User.objects.create(
                username=username,
                is_staff=True
            )
            user.set_password(password)
            user.save()
            login(req, user)

            return JsonResponse({'message': 'success', 'errors': errors})                


class LoginViewAPI(View):

    @method_decorator(csrf_exempt, name='dispatch')
    def dispatch(self, req, **kwargs):
        return super().dispatch(req, **kwargs)
    
    def post(self, req, *args, **kwargs):

        username = req.POST.get('username', '').strip().lower()
        password = req.POST.get('password', '')
        
        user = authenticate(username=username, password=password)
        if user:
            login(req, user)

            return JsonResponse({'message': 'success'})
                
        return JsonResponse({'message': 'failed'})


class UserTypeAPI(View):

    def get(self, req, *args, **kwargs):

        if req.user.is_authenticated:
            return JsonResponse({'user': req.user.role})
        else:
            return JsonResponse({'user': 'guest'})


class PasswordChangeAPI(CSRFExempt, LoginRequiredMixin, View):

    def post(self, req, *args, **kwargs):

        current_password = req.POST.get('current_password')
        new_password = req.POST.get('new_password')

        data = {
            'message': 'failed',
            'errors': []
        }

        if not 7 < len(new_password) < 100:
            data['errors'] = ["new_password"]
        
        if not data['errors']:
            user = authenticate(username=req.user.username, password=current_password)
            if user:
                user.set_password(new_password)
                user.save()

                login(req, user)

                data['message'] = 'success'

            else:
                data["errors"] = ["current_password"]
        

        return JsonResponse(data, safe=False)
