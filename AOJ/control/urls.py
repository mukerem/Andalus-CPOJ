from django.urls import path, include
from . import views

urlpatterns = [
    path('score-values/', views.score_values, name='score_values'),
    path('edit-score-values/<int:score_id>/', views.edit_score_values, name='edit_score_values'),
    path('language-list/', views.language_list, name='language_list'),
    path('language/edit/<int:language_id>/', views.edit_language, name='edit_language'),    
    path('language/delete/<int:language_id>/', views.delete_language, name='delete_language'),
    path('language/delete-done/<int:language_id>/', views.delete_language_done, name='delete_language_done'),
    path('language-register/', views.language_register, name='language_register'),
]
