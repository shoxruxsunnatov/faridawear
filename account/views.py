from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from admins.views import ProfileView as TeacherProfileView


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'teachers/profile.html'
    

    def get(self, req, *args, **kwargs):
        if req.user.role in ('admin', 'supervisor'):
            view = TeacherProfileView.as_view()
        
        
        return view(req, *args, **kwargs)


    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        
        return context


class PasswordChangeView(LoginRequiredMixin, TemplateView):
    template_name = 'students/password_change.html'
