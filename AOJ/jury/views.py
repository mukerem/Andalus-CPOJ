from django.shortcuts import render
from problem.models import Problem
from contest.models import Contest
from authentication.models import User
from competitive.models import Submit
from django.contrib.auth.decorators import login_required
from authentication.decorators import jury_auth, jury_auth_and_contest_exist
from django.utils import timezone


@login_required
def jury_homepage(request):
    return render(request, 'jury_homepage.html')


@login_required
@jury_auth
def jury_user_list(request):
    contestant_user = User.objects.filter(role__short_name="contestant").order_by('username')
    admin_user = User.objects.filter(role__short_name="admin").order_by('username')
    jury_user = User.objects.filter(role__short_name="jury").order_by('username')
    return render(request, 'jury_user_list.html', {'contestant_user': contestant_user, 'admin_user': admin_user, 'jury_user': jury_user})


@login_required
@jury_auth
def jury_view_problem(request):
    total_problems = Problem.objects.all().order_by('title')
    return render(request, 'jury_problem_list.html', {'problem': total_problems})


@login_required
@jury_auth
def jury_contest_list(request):
    total_contest = Contest.objects.all().order_by('start_time').reverse()
    now = timezone.now()
    for contest in total_contest:
        if now < contest.active_time:
            contest.status = "not active"
        elif now < contest.start_time:
            contest.status = "active"
        elif contest.start_time <= now and now < contest.end_time:
            contest.status = "on going"
        elif contest.end_time <= now and now < contest.deactivate_time:
            contest.status = "end"
        else:
            contest.status = "deactivate"  
    return render(request, 'jury_contest_list.html', {'contest': total_contest})


@login_required
@jury_auth_and_contest_exist
def jury_contest_detail(request, contest_id):
    total_contest = Contest.objects.all().order_by('start_time').reverse()
    now = timezone.now()
    for contest in total_contest:
        if now < contest.active_time:
            contest.status = "not active"
        elif now < contest.start_time:
            contest.status = "active"
        elif contest.start_time <= now and now < contest.end_time:
            contest.status = "on going"
        elif contest.end_time <= now and now < contest.deactivate_time:
            contest.status = "end"
        else:
            contest.status = "deactivate" 
    contest = Contest.objects.get(pk=contest_id)
    return render(request, 'jury_contest_detail.html', {'total_contest': total_contest,'this_contest': contest})
