from django.urls import path

from account.views import (
    ProfileView,
    PasswordChangeView,
)
from account.api import (
    PasswordChangeAPI,
)


app_name = 'account'

urlpatterns = [
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/password-change/', PasswordChangeView.as_view(), name='password_change'),

    # APIs
    path('api/profile/password-change/', PasswordChangeAPI.as_view(), name='password_change_api'),
]
