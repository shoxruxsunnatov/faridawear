from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.views import View

from account.models import User

from account.security import AdminRoleRequired


class TopicsView(AdminRoleRequired, TemplateView):
    template_name = 'teachers/topics.html'


class TopicDetailView(AdminRoleRequired, TemplateView):
    template_name = 'teachers/topic_detail.html'


class GroupsListView(AdminRoleRequired, TemplateView):
    template_name = 'teachers/groups_list.html'
    

class GroupDetailView(AdminRoleRequired, TemplateView):
    template_name = 'teachers/group_detail.html'
    

class StudentDetailView(AdminRoleRequired, View):

    def get(self, req, pk, *args, **kwargs):
        student = get_object_or_404(User, id=pk, role='student')

        data = {
            "student": student
        }
        return render(req, 'teachers/student_detail.html', data)


class ExamsView(AdminRoleRequired, TemplateView):
    template_name = 'teachers/exams_list.html'


class ProfileView(AdminRoleRequired, TemplateView):
    template_name = 'admins/profile.html'


class ExamDetailView(AdminRoleRequired, TemplateView):
    template_name = 'teachers/exam_detail.html'


class StudentResultsView(AdminRoleRequired, TemplateView):
    template_name = 'teachers/results.html'


class VocabularPackagesView(AdminRoleRequired, TemplateView):
    template_name = 'teachers/vocabulary_packages.html'


class VocabularyPackageDetailView(AdminRoleRequired, TemplateView):
    template_name = 'teachers/vocabulary_package_detail.html'


class DictionaryExamsView(AdminRoleRequired, TemplateView):
    template_name = 'teachers/dictionary_exams_list.html'


class DictionaryExamDetailView(AdminRoleRequired, TemplateView):
    template_name = 'teachers/dictionary_exam_detail.html'


class ScheduledExamsView(AdminRoleRequired, TemplateView):
    template_name = 'teachers/scheduled_exams.html'


class ScheduledExamDetailView(AdminRoleRequired, TemplateView):
    template_name = 'teachers/room_session_detail.html'

