from django.views.generic import TemplateView


class TeacherStudentPaymentView(TemplateView):
    template_name = 'teachers/student_payment.html'

