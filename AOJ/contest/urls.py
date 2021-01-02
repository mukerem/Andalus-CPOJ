from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('view/', views.contest_list, name='contest'),
    path('add/', views.addContest, name='add_contest'),
    path('edit/<int:contest_id>/', views.edit_contest, name='edit_contest'),
    path('delete/<int:contest_id>/', views.delete_contest, name='delete_contest'),
    path('delete-done/<int:contest_id>/', views.delete_contest_done, name='delete_contest_done'),
    path('load-contest/contestant/', views.load_contest_in_contestant, name='ajax_load_contest_contestant'),
    path('load-contest/admin/', views.load_contest_in_admin, name='ajax_load_contest_admin'),
    path('load-contest/public/', views.load_contest_in_public, name='ajax_load_contest_public'),

   ]
