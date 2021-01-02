from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('home/', views.jury_homepage, name='jury_homepage'),
    path('problem/', views.jury_view_problem, name='jury_view_problem'),
    path('contest/', views.jury_contest_list, name='jury_contest_list'),
    path('contest/detail/<contest_id>/', views.jury_contest_detail, name='jury_contest_detail'),
    path('user/', views.jury_user_list, name='jury_view_user'),   
]

