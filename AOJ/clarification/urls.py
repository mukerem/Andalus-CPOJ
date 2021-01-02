from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('request/', views.request_clarification, name='request_clarification'),
    path('view/', views.view_clarification, name='view_clarification'),
    path('view-jury/', views.view_jury_clarification, name='view_jury_clarification'),
    path('list/', views.clarification_list, name='clarification_list'),
    path('answered/', views.answered_clarification, name='answered_clarification'),
    path('new/', views.new_clarification_by_admin, name='new_clarification'),
    path('answer/<int:clarification_id>/', views.clarification_answer, name='clarification_answer'),
    path('edit/<int:clarification_id>/', views.edit_clarification, name='edit_clarification'),
   ]