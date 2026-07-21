from django.contrib.auth.views import LogoutView
from django.views.generic import TemplateView, View
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin


# class DashboardView(LoginRequiredMixin, TemplateView):
#     template_name = "admins/dashboard.html"

class DashboardView(LoginRequiredMixin, View):
    def get(self, req, *args, **kwargs):

        if req.user.role in ("admin", "supervisor"):
            return render(req, "sales/pos.html")

        elif req.user.role == "sales":
            return render(req, "sales/pos.html")


class CustomLogoutView(LogoutView):
    next_page = 'main:login'
 

class RegisterView(TemplateView):
    template_name = 'register.html'

    def post(self, req, *args, **kwargs):

        username = req.POST.get('username', '').strip().lower()
        password = req.POST.get('password')
        action = req.POST.get('action')

        self.context = {
            'username': username,
            'password': password
        }
        
        if action == 'login':
            user = authenticate(username=username, password=password)
            if user:
                login(req, user)

                return redirect('main:home')
            
        elif action == 'register' and not action:
            fullname = req.POST.get('fullname', '')
            password_repeat = req.POST.get('password-repeat')

            self.context['fullname'] = fullname
            self.context['password_repeat'] = password_repeat
            self.context.update({
                'fullname': fullname,
                'password_repeat': password_repeat,
                'action': 'register'
            })

            if password_repeat != password:
                self.context['password_repeat_error'] = 'is-invalid'
                return super().get(req, *args, **kwargs)
            
            if User.objects.filter(username=username).first():
                self.context['username_error'] = 'is-invalid'
                return super().get(req, *args, **kwargs)
                
        return redirect('main:register')


    def get(self, req, *args, **kwargs):

        if req.user.is_authenticated:
            
            return redirect('main:home')
        
        return super().get(req, *args, **kwargs)


class AboutView(TemplateView):
    template_name = 'about.html'


class LoginView(View):
    
    def get(self, req, *args, **kwargs):

        if req.user.is_authenticated:
            return redirect("/")
        else:
            return render(req, "login.html")

