from django.urls import path

from main.views import (
    RegisterView,
    DashboardView,
    CustomLogoutView,
    AboutView,
    LoginView
)

app_name = 'main'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('log-out/', CustomLogoutView.as_view(), name='log-out'),
    path('about/', AboutView.as_view(), name='about'),
    path('', DashboardView.as_view(), name='dashboard')
]