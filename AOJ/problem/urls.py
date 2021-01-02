from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('list/', views.problem_list, name='problem_list'),
    path('add/', views.addProblem, name='add_problem'),
    path('add-zip/', views.addProblemZIP, name='add_problem_zip'),
    path('edit/<int:problem_id>/', views.edit_problem, name='edit_problem'),
    path('delete/<int:problem_id>/', views.delete_problem, name='delete_problem'),
    path('delete-done/<int:problem_id>/', views.delete_problem_done, name='delete_problem_done'),
    path('testcase/<int:problem_id>/', views.testcase, name='testcase'),
    path('delete-testcase/<int:testcase_id>/', views.delete_testcase, name='delete_testcase'),
    path('delete-testcase-done/<int:testcase_id>/', views.delete_testcase_done, name='delete_testcase_done'),

]