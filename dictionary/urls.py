from django.urls import path

from dictionary.views import (
    VocabularyPackagesView,
    VocabularyPackageDetailView,
    MyVocabularyPackageDetailView,
    DictionaryExamsView,
    DictionaryExamDetailView,
    DictionaryTrainingExamsView,
    PrintVocabularyPackageView,
    PrintMyVocabularyPackageView,
    VocabularyDetailView,
    MyDictionaryView
)
from dictionary.api import (
    VocabularyPackagesViewAPI,
    MyVocabularyPackagesViewAPI,
    VocabularyPackageDetailViewAPI,
    MyVocabularyPackageDetailViewAPI,
    VocabularyAPI,
    MyVocabularyAPI,
    VocabularyDetailAPI,
    MyVocabularyDetailAPI,
    VocabularyDetailViewAPI,
    VocabularyChartAPI,
    DictionaryExamsViewAPI,
    DictionaryExamDetailViewAPI,
    GetOngoingExamAPI,
    SubmitAnswerAPI,
    DictionaryExamSessionsListAPI,
    RecordPenaltyAPI,
    ResetPenaltyAPI,
    LockStatusAPI,
    EndExamSessionAPI,
    DictionaryTrainingExamsViewAPI,
    PrintVocabularyPackageViewAPI,
    PrintMyVocabularyPackageViewAPI,
    RegenerateVocabularyAPI
)

app_name = 'dictionary'

urlpatterns = [
    path('dictionary/', VocabularyPackagesView.as_view(), name='vocabulary_packages'),
    path('dictionary/packages/<int:pk>/', VocabularyPackageDetailView.as_view(), name='vocabulary_packages'),
    path('my-dictionary/packages/<int:pk>/', MyVocabularyPackageDetailView.as_view(), name='vocabulary_packages'),
    path('dictionary/packages/<int:pk>/print/', PrintVocabularyPackageView.as_view(), name='print_package'),
    path('my-dictionary/packages/<int:pk>/print/', PrintMyVocabularyPackageView.as_view(), name='print_my_package'),
    path('dictionary/packages/<int:package_id>/<int:pk>/', VocabularyDetailView.as_view(), name='vocabulary_detail'),
    path('dictionary/exams/', DictionaryExamsView.as_view(), name='exams_list'),
    path('dictionary/exams/<int:pk>/', DictionaryExamDetailView.as_view(), name='exam_detail'),
    path('dictionary/training/', DictionaryTrainingExamsView.as_view(), name='training_exams_list'),
    path('my-dictionary/', MyDictionaryView.as_view(), name='my_dictionary'),


    # APIs
    path('api/dictionary/packages/', VocabularyPackagesViewAPI.as_view(), name="vocabulary_packages_api"),
    path('api/my-dictionary/packages/', MyVocabularyPackagesViewAPI.as_view(), name="my_vocabulary_packages_api"),
    path('api/dictionary/packages/<int:pk>/', VocabularyPackageDetailViewAPI.as_view(), name="vocabulary_package_detail_view_api"),
    path('api/my-dictionary/packages/<int:pk>/', MyVocabularyPackageDetailViewAPI.as_view(), name="my_vocabulary_package_detail_view_api"),
    path('api/dictionary/packages/<int:pk>/print/', PrintVocabularyPackageViewAPI.as_view(), name="print_vp_api"),
    path('api/my-dictionary/packages/<int:pk>/print/', PrintMyVocabularyPackageViewAPI.as_view(), name="print_my_vp_api"),
    path('api/dictionary/packages/<int:pk>/vocabularies/', VocabularyAPI.as_view(), name="vocabularies_api"),
    path('api/my-dictionary/packages/<int:pk>/vocabularies/', MyVocabularyAPI.as_view(), name="my_vocabularies_api"),
    path('api/dictionary/packages/<int:package_id>/vocabularies/<int:pk>/', VocabularyDetailAPI.as_view(), name="vocabulary_detail_api"),
    path('api/my-dictionary/packages/<int:package_id>/vocabularies/<int:pk>/', MyVocabularyDetailAPI.as_view(), name="my_vocabulary_detail_api"),
    path('api/my-dictionary/regenerate/<int:pk>/', RegenerateVocabularyAPI.as_view(), name="regenerate_vocabulary_api"),
    path('api/dictionary/packages/<int:package_id>/<int:pk>/', VocabularyDetailViewAPI.as_view(), name="vocabulary_detail_view_api"),
    path('api/dictionary/packages/chart/', VocabularyChartAPI.as_view(), name="vocabulary_chart_api"),
    path('api/dictionary/exams/', DictionaryExamsViewAPI.as_view(), name="exams_list_api"),
    path('api/dictionary/exams/<int:pk>/', DictionaryExamDetailViewAPI.as_view(), name='exam_detail_view_api'),
    path('api/dictionary/exams/ongoing/', GetOngoingExamAPI.as_view(), name='ongoing_exam_api'),
    path('api/dictionary/exams/submit/', SubmitAnswerAPI.as_view(), name='submit_answer_api'),
    path('api/dictionary/exams/<int:pk>/exam-sessions/', DictionaryExamSessionsListAPI.as_view(), name='exam_sessions_list_api'),
    path('api/dictionary/exams/penalty/', RecordPenaltyAPI.as_view(), name='record_penalty_api'),
    path('api/dictionary/exams/penalty/reset/', ResetPenaltyAPI.as_view(), name='reset_penalty_api'),
    path('api/dictionary/exams/lock-status/', LockStatusAPI.as_view(), name='lock_status_api'),
    path('api/dictionary/exams/end/', EndExamSessionAPI.as_view(), name='end_exam_session_api'),
    path('api/dictionary/training/', DictionaryTrainingExamsViewAPI.as_view(), name='training_exams_list_api'),

]