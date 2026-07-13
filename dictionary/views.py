from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from account.security import AdminRoleRequired

from admins.views import (
    VocabularPackagesView as TeacherVocabularyPackagesView,
    VocabularyPackageDetailView as TeacherVocabularyPackageDetailView,
    DictionaryExamsView as TeacherDictionaryExamsView,
    DictionaryExamDetailView as TeacherDictionaryExamDetailView,
)
from students.views import (
    VocabularPackagesView as StudentVocabularyPackagesView,
    DictionaryExamsView as StudentDictionaryExamsView,
    VocabularyPackageDetailView as StudentVocabularyPackageDetailView,
    DictionaryExamDetailView as StudentDictionaryExamDetailView
)
from dictionary.utils import delete_expired_exams


class VocabularyPackagesView(LoginRequiredMixin, View):

    def get(self, req, *args, **kwargs):
        if req.user.role in ('teacher', 'supervisor'):
            view = TeacherVocabularyPackagesView.as_view()
        else:
            view = StudentVocabularyPackagesView.as_view()
        
        return view(req, *args, **kwargs)


class VocabularyPackageDetailView(LoginRequiredMixin, View):

    def get(self, req, *args, **kwargs):
        
        if req.user.role in ('teacher', 'supervisor'):
            view = TeacherVocabularyPackageDetailView.as_view()
        else:
            view = StudentVocabularyPackageDetailView.as_view()
        
        return view(req, *args, **kwargs)


class MyVocabularyPackageDetailView(LoginRequiredMixin, View):

    def get(self, req, *args, **kwargs):

        return render(req, 'students/my_vocabulary_package_detail.html')


class DictionaryExamsView(LoginRequiredMixin, View):

    def get(self, req, *args, **kwargs):

        delete_expired_exams()
        
        if req.user.role in ('teacher', 'supervisor'):
            view = TeacherDictionaryExamsView.as_view()
        else:
            view = StudentDictionaryExamsView.as_view()
        
        return view(req, *args, **kwargs)


class DictionaryExamDetailView(LoginRequiredMixin, View):

    def get(self, req, *args, **kwargs):
        if req.user.role in ('teacher', 'supervisor'):
            view = TeacherDictionaryExamDetailView.as_view()
        else:
            view = StudentDictionaryExamDetailView.as_view()
        
        return view(req, *args, **kwargs)


class DictionaryTrainingExamsView(LoginRequiredMixin, View):

    def get(self, req, *args, **kwargs):

        delete_expired_exams()
        
        return render(req, 'students/dictionary_training_exams_list.html')
    

class PrintVocabularyPackageView(AdminRoleRequired, View):

    def get(self, req, pk, *args, **kwargs):

        return render(req, 'teachers/print_package.html')


class PrintMyVocabularyPackageView(View):

    def get(self, req, pk, *args, **kwargs):

        return render(req, 'students/print_package.html')


class VocabularyDetailView(LoginRequiredMixin, View):

    def get(self, req, pk, *args, **kwargs):

        return render(req, 'teachers/vocabulary_detail.html')


class MyDictionaryView(LoginRequiredMixin, View):

    def get(self, req, *args, **kwargs):

        return render(req, 'students/my_dictionary.html')
