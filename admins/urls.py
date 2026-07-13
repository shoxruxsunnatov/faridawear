from django.urls import path

from admins.views import (
    TopicsView,
    TopicDetailView,
    GroupsListView,
    GroupDetailView,
    StudentDetailView,
    StudentResultsView
)
from admins.api import (
    GroupsListViewAPI,
    GroupDetailViewAPI,
    TopicsListViewAPI,
    TopicDetailViewAPI,
    TestsListViewAPI,
    StudentDetailViewAPI
)


app_name = 'teachers'

urlpatterns = [
    path('teacher/topics/', TopicsView.as_view(), name='topics'),
    path('teacher/topics/<int:pk>/', TopicDetailView.as_view(), name='topic_detail'),
    path('teacher/groups/', GroupsListView.as_view(), name='groups_list'),
    path('teacher/groups/<int:pk>/', GroupDetailView.as_view(), name='group_detail'),
    path('students/<int:pk>/', StudentDetailView.as_view(), name='student_detail'),
    path('students/<int:pk>/results/', StudentResultsView.as_view(), name='student_results'),

    # APIs
    path('api/teacher/groups/', GroupsListViewAPI.as_view(), name='groups_list_view_api'),
    path('api/teacher/groups/<int:pk>/', GroupDetailViewAPI.as_view(), name='groups_detail_view_api'),
    path('api/teacher/topics/', TopicsListViewAPI.as_view(), name='topics_list_view_api'),
    path('api/teacher/topics/<int:pk>/', TopicDetailViewAPI.as_view(), name='topics_detail_view_api'),
    path('api/teacher/topics/<int:pk>/tests/', TestsListViewAPI.as_view(), name='tests_list_view_api'),
    path('api/students/<int:pk>/edit/', StudentDetailViewAPI.as_view(), name='student_detail_view_api'),

]