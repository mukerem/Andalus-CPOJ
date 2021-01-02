from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ClarificationRequest, ClarificationAnswer, NewClarification, EditClarification
from .models import Clarification
from contest.models import Contest
from authentication.decorators import contestant_auth, admin_auth, jury_auth, admin_auth_and_clarification_exist
from django.utils import timezone
from contest.views import refresh_contest_session_public, refresh_contest_session_admin, refresh_contest_session_contestant
# Create your views here.


@login_required
@contestant_auth
def request_clarification(request):
    refresh_contest_session_contestant(request)  # refersh the contest session
    current_contest_id = request.session.get('active_contest_contestant')
    problem_list = None
    try:
        current_contest = Contest.objects.get(
            pk=current_contest_id, active_time__lte=timezone.now(), enable=True)
    except Contest.DoesNotExist:
        current_contest = None
    if current_contest:
        problem_list = current_contest.problem.all().order_by('title')
        if request.method == "POST":
            form = ClarificationRequest(request.POST)
            form.fields['problem'].queryset = problem_list
            if form.is_valid():
                post = form.save(commit=False)
                post.send_time = timezone.now()
                post.user = request.user
                post.contest = current_contest
                post.save()

                return redirect('request_clarification')
        else:
            form = ClarificationRequest()
            form.fields['problem'].queryset = problem_list
    else:
        form = None

    all_clarification = Clarification.objects.filter(
        contest=current_contest, user=request.user).order_by('send_time').reverse()
    for cla in all_clarification:
        if len(cla.question) > 100:
            cla.short_question = cla.question[:100] + '...'
        else:
            cla.short_question = cla.question
    return render(request, 'clarification_request.html', {'form': form, 'all_clarification': all_clarification, 'clar': 'hover'})


@login_required
@contestant_auth
def view_clarification(request):
    refresh_contest_session_contestant(request)  # refersh the contest session
    current_contest_id = request.session.get('active_contest_contestant')
    try:
        current_contest = Contest.objects.get(
            pk=current_contest_id, active_time__lte=timezone.now(), enable=True)
    except Contest.DoesNotExist:
        current_contest = None

    all_clarification = Clarification.objects.filter(contest=current_contest, user=request.user, status=True).order_by('send_time').reverse() |\
        Clarification.objects.filter(
            contest=current_contest, is_public=True, status=True).order_by('send_time').reverse()

    for cla in all_clarification:
        if len(cla.question) > 60:
            cla.short_question = cla.question[:60] + '...'
        else:
            cla.short_question = cla.question

        if len(cla.answer) > 60:
            cla.short_answer = cla.answer[:60] + '...'
        else:
            cla.short_answer = cla.answer

    return render(request, 'view_clarification.html', {'all_clarification': all_clarification, 'clarif': 'hover'})


@login_required
@admin_auth
def clarification_list(request):
    refresh_contest_session_admin(request)  # refersh the contest session
    current_contest_id = request.session.get('active_contest_admin')
    try:
        current_contest = Contest.objects.get(
            pk=current_contest_id, active_time__lte=timezone.now(), enable=True)
    except Contest.DoesNotExist:
        current_contest = None

    all_clarification = Clarification.objects.filter(
        contest=current_contest, status=False).order_by('send_time').reverse()
    for cla in all_clarification:
        if len(cla.question) > 100:
            cla.short_question = cla.question[:100] + '...'
        else:
            cla.short_question = cla.question
    return render(request, 'clarification_list.html', {'all_clarification': all_clarification, 'clar': 'hover'})


@login_required
@admin_auth_and_clarification_exist
def clarification_answer(request, clarification_id):

    clarification = Clarification.objects.get(pk=clarification_id)
    all_clarification = Clarification.objects.filter(
        contest=clarification.contest, status=False).order_by('send_time').reverse()
    for cla in all_clarification:
        if len(cla.question) > 100:
            cla.short_question = cla.question[:100] + '...'
        else:
            cla.short_question = cla.question
    if clarification.problem:
        initial_info = {"_pro": clarification.problem.title,
                        "_user": clarification.user,   "_question": clarification.question}
    else:
        initial_info = {"_pro": "General", "_user": clarification.user,
                        "_question": clarification.question}

    if request.method == "POST":
        form = ClarificationAnswer(
            request.POST, instance=clarification, initial=initial_info)
        if form.is_valid():
            post = form.save(commit=False)
            if post.answer:
                post.status = True
            post.save()
            return redirect('clarification_list')
    else:
        form = ClarificationAnswer(
            instance=clarification, initial=initial_info)

    return render(request, 'clarification_answer.html', {'form': form, 'all_clarification': all_clarification, 'this_clarification_id': clarification.id, 'clar': 'hover'})


@login_required
@admin_auth
def new_clarification_by_admin(request):
    refresh_contest_session_admin(request)  # refersh the contest session
    current_contest_id = request.session.get('active_contest_admin')
    try:
        current_contest = Contest.objects.get(
            pk=current_contest_id, active_time__lte=timezone.now(), enable=True)
    except Contest.DoesNotExist:
        current_contest = None

    if request.method == "POST":
        form = NewClarification(request.POST)
        form.fields['user'].queryset = current_contest.user.filter(
            role__short_name='contestant').order_by('name')
        form.fields['problem'].queryset = current_contest.problem.all().order_by(
            'title')
        if form.is_valid():
            post = form.save(commit=False)
            post.contest = current_contest
            post.question = "new clarification from admin"
            post.send_time = timezone.now()
            if request.POST['user'] and post.is_public:
                post.is_public = False

            post.status = True
            post.save()
            return redirect('clarification_list')
    else:
        form = NewClarification()
        form.fields['user'].queryset = current_contest.user.filter(
            role__short_name='contestant').order_by('name')
        form.fields['problem'].queryset = current_contest.problem.all().order_by(
            'title')
    return render(request, 'new_clarification.html', {'form': form, 'clar': 'hover'})


@login_required
@admin_auth
def answered_clarification(request):
    refresh_contest_session_admin(request)  # refersh the contest session
    current_contest_id = request.session.get('active_contest_admin')
    try:
        current_contest = Contest.objects.get(
            pk=current_contest_id, active_time__lte=timezone.now(), enable=True)
    except Contest.DoesNotExist:
        current_contest = None

    all_clarification = Clarification.objects.filter(
        contest=current_contest, status=True).order_by('send_time').reverse()
    for cla in all_clarification:
        if len(cla.question) > 60:
            cla.short_question = cla.question[:60] + '...'
        else:
            cla.short_question = cla.question
        if len(cla.answer) > 60:
            cla.short_answer = cla.answer[:60] + '...'
        else:
            cla.short_answer = cla.answer
    return render(request, 'answered_clarification_list.html', {'all_clarification': all_clarification, 'clar': 'hover'})


@login_required
@admin_auth_and_clarification_exist
def edit_clarification(request, clarification_id):

    clarification = Clarification.objects.get(pk=clarification_id)
    if clarification.user:
        user = clarification.user.username
    else:
        user = None

    if clarification.problem:
        initial_info = {"_pro": clarification.problem.title,
                        "_question": clarification.question, "_user": user}
    else:
        initial_info = {"_pro": "General",
                        "_question": clarification.question, "_user": user}

    if request.method == "POST":
        form = EditClarification(
            request.POST, instance=clarification, initial=initial_info)
        if form.is_valid():
            post = form.save(commit=False)
            if post.answer:
                post.status = True
            post.save()
            return redirect('clarification_list')
    else:
        form = EditClarification(instance=clarification, initial=initial_info)

    return render(request, 'edit_clarification.html', {'form': form, 'clar': 'hover'})


@login_required
@jury_auth
def view_jury_clarification(request):
    refresh_contest_session_admin(request)  # refersh the contest session
    current_contest_id = request.session.get('active_contest_admin')
    try:
        current_contest = Contest.objects.get(
            pk=current_contest_id, active_time__lte=timezone.now(), enable=True)
    except Contest.DoesNotExist:
        current_contest = None

    all_clarification = Clarification.objects.filter(
        contest=current_contest, status=True).order_by('send_time').reverse()

    for cla in all_clarification:
        if len(cla.question) > 60:
            cla.short_question = cla.question[:60] + '...'
        else:
            cla.short_question = cla.question

        if len(cla.answer) > 60:
            cla.short_answer = cla.answer[:60] + '...'
        else:
            cla.short_answer = cla.answer

    return render(request, 'view_jury_clarification.html', {'all_clarification': all_clarification, 'clar': 'hover'})
