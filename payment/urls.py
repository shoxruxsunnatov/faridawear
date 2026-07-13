from django.urls import path

from payment.views import (
    TeacherStudentPaymentView
)
from payment.api import (
    TeacherStudentPaymentViewAPI,
    StudentPaymentSettingsAPI
)


app_name = 'payment'

urlpatterns = [
    path('students/<int:pk>/payment/', TeacherStudentPaymentView.as_view(), name='teacher_student_payment'),

    # APIs
    path('api/students/<int:pk>/payment/', TeacherStudentPaymentViewAPI.as_view(), name='teacher_student_payment_api'),
    path('api/students/<int:pk>/payment/settings/', StudentPaymentSettingsAPI.as_view(), name='student_payment_settings_api'),
    
]