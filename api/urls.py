from django.urls import path

from account.api import (
    LoginViewAPI,
    UserTypeAPI
)

app_name = 'api'

urlpatterns = [
    path('login/', LoginViewAPI.as_view(), name='login'),
    path('usertype/', UserTypeAPI.as_view(), name='usertype'),

]