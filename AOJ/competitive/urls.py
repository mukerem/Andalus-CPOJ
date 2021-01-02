from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('submit/', views.submit, name='submit'),
    path('problem/', views.active_contest_problem, name='active_contest_problem'),
    path('submit/language/', views.ajax_get_language_list, name='ajax_get_language_list'),
    path('scoreboard/public/', views.public_scoreboard, name='public_scoreboard'),
    path('scoreboard/public/refresh/', views.public_scoreboard_refresh, name='public_scoreboard_refresh'),
    path('scoreboard/jury/', views.jury_scoreboard, name='jury_scoreboard'),
    path('scoreboard/jury/refresh/', views.jury_scoreboard_refresh, name='jury_scoreboard_refresh'),
    path('submissions/contest-select/', views.view_submit_contest_select, name='view_submit_contest_select'),
    path('submissions/<int:contest_id>/', views.view_submissions, name='view_submission'),
    path('submit-detail/<int:submit_id>/', views.submission_detail, name='submission_detail'),
    path('rejudge/filter/', views.rejudge_submission_filter, name='rejudge_submission_filter'),
    path('submission/filter/', views.view_submission_filter, name='view_submission_filter'),
    path('specific-problem-submit/', views.specific_problem_submission, name='specific_problem_submission'),
    path('single-rejudge/<int:submit_id>/', views.single_rejudge, name='single_rejudge'),
    path('multi-rejudge/<int:problem_id>/<int:contest_id>/<int:user_id>/', views.multi_rejudge, name='multi_rejudge'),
    path('rejudge/contest-select/', views.rejudge_contest_select, name='rejudge_contest_select'),
    path('rejudge/submission-list/<int:contest_id>/', views.rejudge_submission_list, name='rejudge_submission_list'),
    path('rejudge/process/', views.ajax_rejudge, name='ajax_rejudge'),
    path('rating/', views.rating, name='rating'),
    path('view-result/<int:contest_id>/', views.deactivate_contest_scoreboard, name='deactivate_contest_scoreboard'),

]


