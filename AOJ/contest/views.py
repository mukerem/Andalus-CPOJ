from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from authentication.decorators import admin_auth, admin_auth_and_contest_exist, contestant_auth,\
    admin_or_jury_auth, admin_jury_auth_and_contest_exist
from .models import Contest
from authentication.models import User
from django.utils import timezone
from .forms import AddContest, EditContest
from django.contrib import messages
import pytz
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.db import IntegrityError
from competitive.models import RankcacheJury, RankcachePublic, ScorecacheJury, ScorecachePublic, Submit
from control.models import Setting


def time_gap(submit_time, contest_start_time):
    td = submit_time - contest_start_time
    time_taken = td.seconds // 60 + td.days * 1440
    return time_taken


def check_base_site(request):
    if request.user.role.short_name == 'admin':
        base = 'admin_base_site.html'
    elif request.user.role.short_name == 'jury':
        base = 'jury_base_site.html'
    elif request.user.role.short_name == 'contestant':
        base = 'contestant_base_site.html'
    elif request.user.role.short_name == 'public':
        base = 'public_base_site.html'
    return base


def create_contest_session_admin(request):
    now = timezone.now()
    all_contests = Contest.objects.filter(
        active_time__lte=now, deactivate_time__gt=now, enable=True)
    if all_contests:
        if all_contests[0].start_time <= now:
            request.session['start_contest_admin'] = str(all_contests[0].pk)

        request.session['active_contest_admin'] = str(all_contests[0].pk)
        request.session['all_active_contest_list_admin'] = [
            (i.pk, i.short_name) for i in all_contests]
        request.session['current_contest_start_time'] = str(
            all_contests[0].start_time)
        request.session['current_contest_end_time'] = str(
            all_contests[0].end_time)
        if len(request.session['all_active_contest_list_admin']) == 1:
            request.session['all_active_contest_list_admin'] = None
    else:
        if 'start_contest_admin' in request.session:
            del request.session['start_contest_admin']
        if 'active_contest_admin' in request.session:
            del request.session['active_contest_admin']
            if 'current_contest_start_time' in request.session:
                del request.session['current_contest_start_time']
                del request.session['current_contest_end_time']
        if 'all_active_contest_list_admin' in request.session:
            del request.session['all_active_contest_list_admin']


def create_contest_session_contestant(request):
    now = timezone.now()
    all_contests = Contest.objects.filter(
        user=request.user, active_time__lte=now, deactivate_time__gte=now, enable=True).order_by('title')
    if all_contests:
        if all_contests[0].start_time <= now:
            request.session['start_contest_contestant'] = str(
                all_contests[0].pk)

        request.session['active_contest_contestant'] = str(all_contests[0].pk)
        request.session['current_contest_start_time'] = str(
            all_contests[0].start_time)
        request.session['current_contest_end_time'] = str(
            all_contests[0].end_time)
        request.session['all_active_contest_list_contestant'] = [
            (i.pk, i.short_name) for i in all_contests]
        if len(request.session['all_active_contest_list_contestant']) == 1:
            request.session['all_active_contest_list_contestant'] = None
    else:
        if 'start_contest_contestant' in request.session:
            del request.session['start_contest_contestant']
        if 'active_contest_contestant' in request.session:
            del request.session['active_contest_contestant']
            if 'current_contest_start_time' in request.session:
                del request.session['current_contest_start_time']
                del request.session['current_contest_end_time']
        if 'all_active_contest_list_contestant' in request.session:
            del request.session['all_active_contest_list_contestant']


def create_contest_session_public(request):
    now = timezone.now()
    all_contests = Contest.objects.filter(
        is_public=True, active_time__lte=now, deactivate_time__gte=now, enable=True).order_by('title')
    if all_contests:
        if all_contests[0].start_time <= now:
            request.session['start_contest_public'] = str(all_contests[0].pk)

        request.session['active_contest_public'] = str(all_contests[0].pk)
        request.session['current_contest_start_time'] = str(
            all_contests[0].start_time)
        request.session['current_contest_end_time'] = str(
            all_contests[0].end_time)
        request.session['all_active_contest_list_public'] = [
            (i.pk, i.short_name) for i in all_contests]
        if len(request.session['all_active_contest_list_public']) == 1:
            request.session['all_active_contest_list_public'] = None
    else:
        if 'start_contest_public' in request.session:
            del request.session['start_contest_public']
        if 'active_contest_public' in request.session:
            del request.session['active_contest_public']
            if 'current_contest_start_time' in request.session:
                del request.session['current_contest_start_time']
                del request.session['current_contest_end_time']
        if 'all_active_contest_list_public' in request.session:
            del request.session['all_active_contest_list_public']


def refresh_contest_session_admin(request):
    now = timezone.now()
    all_contests = Contest.objects.filter(
        active_time__lte=now, deactivate_time__gte=now, enable=True)
    if 'active_contest_admin' in request.session:
        try:
            Contest.objects.get(pk=request.session.get(
                'active_contest_admin'), active_time__lte=now, deactivate_time__gte=now, enable=True)
        except Contest.DoesNotExist:
            del request.session['active_contest_admin']
            if 'current_contest_start_time' in request.session:
                del request.session['current_contest_start_time']
                del request.session['current_contest_end_time']

    if 'start_contest_admin' in request.session:
        try:
            Contest.objects.get(pk=request.session.get(
                'start_contest_admin'), start_time__lte=now, deactivate_time__gte=now, enable=True)
        except Contest.DoesNotExist:
            del request.session['start_contest_admin']

    if 'active_contest_admin' in request.session:
        try:
            current_contest = Contest.objects.get(
                pk=request.session.get('active_contest_admin'))
            if current_contest.start_time <= now and not 'start_contest_admin' in request.session:
                request.session['start_contest_admin'] = str(
                    current_contest.pk)

            request.session['current_contest_start_time'] = str(
                current_contest.start_time)
            request.session['current_contest_end_time'] = str(
                current_contest.end_time)
        except Contest.DoesNotExist:
            pass
    else:
        if all_contests:
            request.session['active_contest_admin'] = all_contests[0].pk
            if all_contests[0].start_time <= now:
                request.session['start_contest_admin'] = str(
                    all_contests[0].pk)

    if all_contests:
        request.session['all_active_contest_list_admin'] = [
            (i.pk, i.short_name) for i in all_contests]
        if len(request.session['all_active_contest_list_admin']) == 1:
            request.session['all_active_contest_list_admin'] = None
    elif 'all_active_contest_list_admin' in request.session:
        del request.session['all_active_contest_list_admin']
    if 'current_contest_start_time' in request.session and not 'active_contest_admin' in request.session:
        del request.session['current_contest_start_time']
        del request.session['current_contest_end_time']


def refresh_contest_session_contestant(request):
    now = timezone.now()
    all_contests = Contest.objects.filter(
        user=request.user, active_time__lte=now, deactivate_time__gte=now, enable=True)
    if 'active_contest_contestant' in request.session:
        try:
            Contest.objects.get(pk=request.session.get('active_contest_contestant'),
                                user=request.user, active_time__lte=now, deactivate_time__gte=now, enable=True)
        except Contest.DoesNotExist:
            del request.session['active_contest_contestant']

    if 'start_contest_contestant' in request.session:
        try:
            Contest.objects.get(pk=request.session.get('start_contest_contestant'),
                                user=request.user, start_time__lte=now, deactivate_time__gte=now, enable=True)
        except Contest.DoesNotExist:
            del request.session['start_contest_contestant']

    if 'active_contest_contestant' in request.session:
        contest = Contest.objects.get(
            pk=request.session.get('active_contest_contestant'))
        if contest.start_time <= now and not 'start_contest_contestant' in request.session:
            request.session['start_contest_contestant'] = str(contest.pk)

    else:
        if all_contests:
            request.session['active_contest_contestant'] = all_contests[0].pk
            if all_contests[0].start_time <= now:
                request.session['start_contest_contestant'] = str(
                    all_contests[0].pk)

    if 'active_contest_contestant' in request.session:
        try:
            current_contest = Contest.objects.get(
                pk=request.session.get('active_contest_contestant'))
            request.session['current_contest_start_time'] = str(
                current_contest.start_time)
            request.session['current_contest_end_time'] = str(
                current_contest.end_time)
        except Contest.DoesNotExist:
            pass
    if all_contests:
        request.session['all_active_contest_list_contestant'] = [
            (i.pk, i.short_name) for i in all_contests]
        if len(request.session['all_active_contest_list_contestant']) == 1:
            request.session['all_active_contest_list_contestant'] = None
    elif 'all_active_contest_list_contestant' in request.session:
        del request.session['all_active_contest_list_contestant']
    if 'current_contest_start_time' in request.session and not 'active_contest_contestant' in request.session:
        del request.session['current_contest_start_time']
        del request.session['current_contest_end_time']


def refresh_contest_session_public(request):
    now = timezone.now()
    all_contests = Contest.objects.filter(
        active_time__lte=now, deactivate_time__gte=now, enable=True, is_public=True)
    if 'active_contest_public' in request.session:
        try:
            Contest.objects.get(pk=request.session.get('active_contest_public'),
                                active_time__lte=now, deactivate_time__gte=now, enable=True, is_public=True)
        except Contest.DoesNotExist:
            del request.session['active_contest_public']

    if 'start_contest_public' in request.session:
        try:
            Contest.objects.get(pk=request.session.get('start_contest_public'),
                                start_time__lte=now, deactivate_time__gte=now, enable=True, is_public=True)
        except Contest.DoesNotExist:
            del request.session['start_contest_public']

    if 'active_contest_public' in request.session:
        contest = Contest.objects.get(
            pk=request.session.get('active_contest_public'))
        if contest.start_time <= now and not 'start_contest_public' in request.session:
            request.session['start_contest_public'] = str(contest.pk)

    else:
        if all_contests:
            request.session['active_contest_public'] = all_contests[0].pk
            if all_contests[0].start_time <= now:
                request.session['start_contest_public'] = str(
                    all_contests[0].pk)

    if 'active_contest_public' in request.session:
        try:
            current_contest = Contest.objects.get(
                pk=request.session.get('active_contest_public'))
            request.session['current_contest_start_time'] = str(
                current_contest.start_time)
            request.session['current_contest_end_time'] = str(
                current_contest.end_time)
        except Contest.DoesNotExist:
            pass
    if all_contests:
        request.session['all_active_contest_list_public'] = [
            (i.pk, i.short_name) for i in all_contests]
        if len(request.session['all_active_contest_list_public']) == 1:
            request.session['all_active_contest_list_public'] = None
    elif 'all_active_contest_list_public' in request.session:
        del request.session['all_active_contest_list_public']
    if 'current_contest_start_time' in request.session and not 'active_contest_public' in request.session:
        del request.session['current_contest_start_time']
        del request.session['current_contest_end_time']


@login_required
@admin_auth
def contest_list(request):
    refresh_contest_session_admin(request)  # refersh the contest session
    total_contest = Contest.objects.all().order_by('start_time').reverse()
    now = timezone.now()
    for contest in total_contest:
        if contest.enable == False:
            contest.status = "disable"
        elif now < contest.active_time:
            contest.status = "not active"
        elif now < contest.start_time:
            contest.status = "active"
        elif contest.start_time <= now and now < contest.end_time:
            contest.status = "on going"
        elif contest.end_time <= now and now < contest.deactivate_time:
            contest.status = "end"
        else:
            contest.status = "deactivate"
    return render(request, 'contest_list.html', {'contest': total_contest, 'cont': 'hover'})


# def contset_session(contest):
#     user_list = contest.user.all()
#     for user in user_list:
#         try:
#             cont = ContestSession.objects.get(user=user)
#             if cont.contest == contest:
#                 continue
#             cont.contest = contest
#             cont.save()
#         except ContestSession.DoesNotExist:
#             cont = ContestSession(user=user, contest=contest)
#             cont.save()

@login_required
@admin_auth
def addContest(request):
    refresh_contest_session_admin(request)  # refersh the contest session
    if request.method == "POST":
        form = AddContest(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            form.save_m2m()
            # contset_session(post)
            if post.last_update >= post.start_time:
                post.last_update = post.start_time
                # post.last_update = post.start_time - 1 # the correct one is this in seyar shop
                post.save()
            return redirect('contest')
    else:
        form = AddContest()
    return render(request, 'add_contest.html', {'form': form, 'cont': 'hover'})


def rank_update_unfrozen(contest):
    total_rank_cache = RankcacheJury.objects.filter(contest=contest)
    for jury_rank in total_rank_cache:
        try:
            public_rank_cache = RankcachePublic.objects.get(
                user=jury_rank.user, contest=jury_rank.contest)
        except RankcachePublic.DoesNotExist:
            public_rank_cache = RankcachePublic(
                user=jury_rank.user, contest=jury_rank.contest)
            public_rank_cache.save()
        public_rank_cache.point = jury_rank.point
        public_rank_cache.punish_time = jury_rank.punish_time
        public_rank_cache.save()
        total_score_cache = ScorecacheJury.objects.filter(rank_cache=jury_rank)
        for jury_score in total_score_cache:
            try:
                public_score_cache = ScorecachePublic.objects.get(
                    rank_cache=public_rank_cache, problem=jury_score.problem)
            except ScorecachePublic.DoesNotExist:
                public_score_cache = ScorecachePublic(
                    rank_cache=public_rank_cache, problem=jury_score.problem)
                public_score_cache.save()
            public_score_cache.submission = jury_score.submission
            public_score_cache.punish = jury_score.punish
            public_score_cache.correct_submit_time = jury_score.correct_submit_time
            public_score_cache.is_correct = jury_score.is_correct
            public_score_cache.pending = 0
            public_score_cache.save()


def create_new_rank(contest, all_submit):
    for user in contest.user.all():
        if not all_submit.filter(user=user):
            continue
        try:
            rank_cache = RankcacheJury.objects.get(contest=contest, user=user)
            rank_cache.point = 0
            rank_cache.punish_time = 0
            rank_cache.save()
        except RankcacheJury.DoesNotExist:
            rank_cache = RankcacheJury(contest=contest, user=user)
            rank_cache.save()
        for problem in contest.problem.all():
            submit = all_submit.filter(
                user=user, problem=problem).order_by('submit_time')
            if not submit:
                continue
            try:
                score_cache = ScorecacheJury.objects.get(
                    rank_cache=rank_cache, problem=problem)
                score_cache.submission = 0
                score_cache.punish = 0
                score_cache.is_correct = False
                score_cache.correct_submit_time = None
                score_cache.save()
            except ScorecacheJury.DoesNotExist:
                score_cache = ScorecacheJury(
                    rank_cache=rank_cache, problem=problem)
                score_cache.save()

            for sub in submit:
                score_cache.submission += 1
                if sub.result == "Correct":
                    score_cache.is_correct = True
                    score_cache.correct_submit_time = sub.submit_time
                    rank_cache.point = float(
                        rank_cache.point) + float(problem.point)
                    try:
                        punish_value = Setting.objects.get(
                            name="punish time").value
                        rank_cache.punish_time += punish_value * score_cache.punish + \
                            time_gap(score_cache.correct_submit_time,
                                     contest.start_time)
                    except Setting.DoesNotExist:
                        rank_cache.punish_time += 20 * score_cache.punish
                    rank_cache.save()
                    break
                elif sub.result == "Compiler Error":
                    pass
                else:
                    score_cache.punish += 1
            score_cache.save()


def public_rank_create_frozen(contest, all_submit):
    for user in contest.user.all():
        if not all_submit.filter(user=user):
            continue
        try:
            rank_cache = RankcachePublic.objects.get(
                contest=contest, user=user)
            rank_cache.point = 0
            rank_cache.punish_time = 0
            rank_cache.save()
        except RankcachePublic.DoesNotExist:
            rank_cache = RankcachePublic(contest=contest, user=user)
            rank_cache.save()
        for problem in contest.problem.all():
            submit = all_submit.filter(
                user=user, problem=problem).order_by('submit_time')
            if not submit:
                continue
            try:
                score_cache = ScorecachePublic.objects.get(
                    rank_cache=rank_cache, problem=problem)
                score_cache.submission = 0
                score_cache.punish = 0
                score_cache.pending = 0
                score_cache.is_correct = False
                score_cache.correct_submit_time = None
                score_cache.save()
            except ScorecachePublic.DoesNotExist:
                score_cache = ScorecachePublic(
                    rank_cache=rank_cache, problem=problem)
                score_cache.save()

            for sub in submit:
                score_cache.submission += 1
                if contest.frozen_time <= sub.submit_time and sub.submit_time < contest.unfrozen_time:
                    score_cache.pending += 1
                elif sub.result == "Correct":
                    score_cache.is_correct = True
                    score_cache.correct_submit_time = sub.submit_time
                    rank_cache.point = float(
                        rank_cache.point) + float(problem.point)
                    try:
                        punish_value = Setting.objects.get(
                            name="punish time").value
                        rank_cache.punish_time += punish_value * score_cache.punish + \
                            time_gap(score_cache.correct_submit_time,
                                     contest.start_time)
                    except Setting.DoesNotExist:
                        rank_cache.punish_time += 20 * score_cache.punish
                    rank_cache.save()
                    break
                elif sub.result == "Compiler Error":
                    pass
                else:
                    score_cache.punish += 1
            score_cache.save()


def remove_user_and_problem(previous_user, previous_problems, contest):
    for user in previous_user:
        if not user in contest.user.all():
            try:
                rank_cache = RankcacheJury.objects.get(
                    contest=contest, user=user)
                rank_cache.delete()
            except RankcacheJury.DoesNotExist:
                pass
            try:
                rank_cache = RankcachePublic.objects.get(
                    contest=contest, user=user)
                rank_cache.delete()
            except RankcachePublic.DoesNotExist:
                pass
    for pro in previous_problems:
        if not pro in contest.problem.all():
            all_score_cache = ScorecacheJury.objects.filter(
                rank_cache__contest=contest, problem=pro)
            for score in all_score_cache:
                score.delete()
            all_score_cache = ScorecachePublic.objects.filter(
                rank_cache__contest=contest, problem=pro)
            for score in all_score_cache:
                score.delete()


def update_rank_score(previous_start_time, previous_end_time, previous_frozen_time, previous_unfrozen_time, previous_user, previous_problems, contest):
    all_submit = Submit.objects.filter(
        contest=contest, submit_time__gte=contest.start_time, submit_time__lt=contest.end_time).order_by('submit_time')
    if previous_start_time != contest.start_time or previous_end_time != contest.end_time or\
            contest.frozen_time != previous_frozen_time or previous_unfrozen_time != contest.unfrozen_time or \
            previous_user != list(contest.user.all()) or previous_problems != list(contest.problem.all()):

        create_new_rank(contest, all_submit)
        if not contest.frozen_time or not(contest.frozen_time <= timezone.now() and timezone.now() < contest.unfrozen_time):
            rank_update_unfrozen(contest)
        else:
            public_rank_create_frozen(contest, all_submit)
    remove_user_and_problem(previous_user, previous_problems, contest)


@login_required
@admin_auth_and_contest_exist
def edit_contest(request, contest_id):
    refresh_contest_session_admin(request)  # refersh the contest session
    contest = Contest.objects.get(pk=contest_id)

    previous_start_time = contest.start_time
    previous_end_time = contest.end_time
    previous_frozen_time = contest.frozen_time
    previous_unfrozen_time = contest.unfrozen_time
    previous_user = list(contest.user.all()).copy()

    if request.method == "POST":
        form = EditContest(request.POST, request.FILES, instance=contest)
        if form.is_valid():
            previous_problems = list(contest.problem.all()).copy()
            post = form.save(commit=False)
            post.last_update = timezone.now()
            post.save()
            form.save_m2m()
            update_rank_score(previous_start_time, previous_end_time, previous_frozen_time,
                              previous_unfrozen_time, previous_user, previous_problems, post)
            # contset_session(post)

            messages.success(request, "The contest " +
                             contest.title+" was update successfully.")
            return redirect('contest')
    else:
        form = EditContest(instance=contest)
    return render(request, 'edit_contest.html', {'form': form, "contest_id": contest.id, 'cont': 'hover'})


@login_required
@admin_auth_and_contest_exist
def delete_contest(request, contest_id):
    refresh_contest_session_admin(request)  # refersh the contest session
    contest = Contest.objects.get(pk=contest_id)
    return render(request, 'delete_contest.html', {'contest': contest, 'cont': 'hover'})


@login_required
@admin_auth_and_contest_exist
def delete_contest_done(request, contest_id):
    refresh_contest_session_admin(request)  # refersh the contest session
    contest = Contest.objects.get(pk=contest_id)
    contest.delete()
    messages.success(request, "The contest " +
                     contest.title + " was deleted successfully.")
    return redirect('contest')


@login_required
@contestant_auth
def load_contest_in_contestant(request):
    refresh_contest_session_contestant(request)  # refersh the contest session
    contest_id = request.GET.get('code')
    request.session['active_contest_contestant'] = contest_id
    now = timezone.now()
    selected_contest = Contest.objects.get(pk=contest_id)
    if selected_contest.start_time <= now:
        request.session['start_contest_contestant'] = contest_id
    elif 'start_contest_contestant' in request.session:
        del request.session['start_contest_contestant']

    request.session['current_contest_start_time'] = str(
        selected_contest.start_time)
    request.session['current_contest_end_time'] = str(
        selected_contest.end_time)
    return HttpResponse('')


@login_required
@admin_or_jury_auth
def load_contest_in_admin(request):
    refresh_contest_session_admin(request)  # refersh the contest session
    contest_id = request.GET.get('code')
    request.session['active_contest_admin'] = contest_id
    now = timezone.now()
    selected_contest = Contest.objects.get(pk=contest_id)
    if selected_contest.start_time <= now:
        request.session['start_contest_admin'] = contest_id
    elif 'start_contest_admin' in request.session:
        del request.session['start_contest_admin']

    request.session['current_contest_start_time'] = str(
        selected_contest.start_time)
    request.session['current_contest_end_time'] = str(
        selected_contest.end_time)
    return HttpResponse('')


def load_contest_in_public(request):
    refresh_active_contest_public(request)  # refersh the contest session
    contest_id = request.GET.get('code')
    request.session['active_contest_public'] = contest_id
    now = timezone.now()
    selected_contest = Contest.objects.get(pk=contest_id)
    if selected_contest.start_time <= now:
        request.session['start_contest_public'] = contest_id
    elif 'start_contest_public' in request.session:
        del request.session['start_contest_public']

    request.session['current_contest_start_time'] = str(
        selected_contest.start_time)
    request.session['current_contest_end_time'] = str(current_contest.end_time)
    return HttpResponse('')
