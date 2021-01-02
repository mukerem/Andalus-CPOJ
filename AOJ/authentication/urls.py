from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('', include('django.contrib.auth.urls')),
    # path('register/', views.Register.as_view(), name='register'),
    path('register/', views.register, name='register'),
    path('home/', views.homepage, name='homepage'),
    path('profile/', views.profile, name='profile'),
    path('profile/password/', views.change_password, name='change_password'),
    path('user/', views.user_list, name='user'),
    path('user/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('user/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('user/delete-done/<int:user_id>/', views.delete_user_done, name='delete_user_done'),
    path('user_register/', views.user_register, name='user_register'),
    path('user_register_csv/', views.user_register_csv, name='user_register_csv'),
    path('setting/', views.setting, name='setting'),
    path('campus-list/', views.campus_list, name='campus_list'),
    path('campus/edit/<int:campus_id>/', views.edit_campus, name='edit_campus'),
    path('campus/delete/<int:campus_id>/', views.delete_campus, name='delete_campus'),
    path('campus/delete-done/<int:campus_id>/', views.delete_campus_done, name='delete_campus_done'),
    path('campus-register/', views.campus_register, name='campus_register'),
    path('generate-password/<str:role_type>/', views.generate_user_password, name='generate_user_password'),
    path('generate-password-done/<str:role_id>/', views.generate_password_done, name='generate_password_done'),

]