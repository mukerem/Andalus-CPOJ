from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from authentication.decorators import contestant_auth, admin_auth, admin_auth_and_submit_exist,\
    admin_auth_and_contest_exist, admin_or_jury_auth, admin_jury_auth_and_contest_exist,\
    admin_jury_auth_and_submit_exist
from django.db import IntegrityError
from django.core.files import File
from contest.models import Contest
from django.utils import timezone
from django.contrib import messages
from .forms import SubmitAnswer
from .models import Language, Submit, TestcaseOutput, ScorecacheJury, ScorecachePublic, RankcacheJury, RankcachePublic
from problem.models import TestCase, Problem
from control.models import Setting
from authentication.views import check_base_site
from authentication.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.core import serializers
import os
import time
import datetime
import math
import json
import subprocess
import sys
from threading import Timer
import multiprocessing
# from asgiref.sync import async_to_sync

from contest.views import rank_update_unfrozen, create_contest_session_admin, create_contest_session_contestant,\
    refresh_contest_session_admin, refresh_contest_session_contestant, refresh_contest_session_public
# from competitive.models import Rankcache_user_public, Rankcache_team_public, Rankcache_user_jury, Rankcache_team_jury,\
#         Scorecache_user_jury, Scorecache_team_jury,Scorecache_user_public, Scorecache_team_public
# from contest.views import user_score_and_rank, team_score_and_rank


def time_gap(submit_time, contest_start_time):
    td = submit_time - contest_start_time
    time_taken = td.seconds // 60 + td.days * 1400
    return time_taken


def setting_values():
    try:
        punish_value = Setting.objects.get(name="punish time").value
    except Setting.DoesNotExist:
        punish_value = 20

    try:
        rating_correct_value = Setting.objects.get(
            name="rating correct value").value
    except Setting.DoesNotExist:
        rating_correct_value = 20

    try:
        rating_punish_value = Setting.objects.get(
            name="rating punish value").value
    except Setting.DoesNotExist:
        rating_punish_value = 1

    return (punish_value, rating_correct_value, rating_punish_value)


def problem_lists(request):
    active_contest_id = request.session.get('active_contest_contestant')
    start_contest_id = request.session.get('start_contest_contestant')

    if not active_contest_id:
        return {'problem': [], 'contest_title': None, 'start_time': None}
    try:
        start_contest = Contest.objects.get(pk=start_contest_id)
        problem = start_contest.problem.all()
    except Contest.DoesNotExist:
        problem = []

    try:
        active_contest = Contest.objects.get(pk=active_contest_id)
        contest_title = active_contest.title
        start_time = active_contest.start_time
    except Contest.DoesNotExist:
        contest_title = None
        start_time = None

    problem = sorted(problem, key=lambda x: x.title.lower())
    return {'problem': problem, 'contest_title': contest_title, 'start_time': start_time, 'pro': 'hover'}


@login_required
@contestant_auth
def active_contest_problem(request):
    refresh_contest_session_contestant(request)  # refersh the contest session
    data = problem_lists(request)
    return render(request, 'problem.html', data)


def convert_to_command(file_name, filename_without_extension, command):
    command = command.replace('#', filename_without_extension)
    command = command.replace('@', file_name)
    return command


def check_absolute_error(correct_answer_list, user_answer_list, error):
    if correct_answer_list and not user_answer_list:
        return 'No Output'
    if len(correct_answer_list) != len(user_answer_list):
        return 'Wrong Answer'
    for testcase_line, user_line in zip(correct_answer_list, user_answer_list):
        correct_line = testcase_line.split()
        user_answer_line = user_line.split()
        if len(correct_line) != len(user_answer_line):
            return 'Wrong Answer'
        for each_correct_answer, each_user_answer in zip(correct_line, user_answer_line):
            if each_correct_answer == each_user_answer:
                continue
            try:
                each_correct_answer = float(each_correct_answer)
                each_user_answer = float(each_user_answer)
            except ValueError:
                return 'Wrong Answer'
            if math.fabs(each_correct_answer - each_user_answer) > error:
                return 'Wrong Answer'

    return 'Correct'

# it must be update for the future work example use diff command


def check_answer(correct_answer_file, user_answer_file, error):
    # if error:
    #     return check_absolute_error(correct_answer_list, user_answer_list, error)
    # else:
    #     signal = os.system("diff {} {}".format(correct_answer_file, user_answer_file))
    #     if signal == 0:
    #         return 'Correct'
    #     elif signal == 256:
    #         return 'Wrong Answer'

    correct_answer = open(correct_answer_file, 'r')
    user_answer = open(user_answer_file, 'r')
    correct_answer_list = []
    user_answer_list = []
    for j in correct_answer:
        x = j.rstrip()
        correct_answer_list.append(x)
    for j in user_answer:
        x = j.rstrip()
        user_answer_list.append(x)
    while correct_answer_list:
        if correct_answer_list[-1]:
            break
        correct_answer_list.pop()

    while user_answer_list:
        if user_answer_list[-1]:
            break
        user_answer_list.pop()
    correct_answer.close()
    user_answer.close()
    if error:
        return check_absolute_error(correct_answer_list, user_answer_list, error)
    else:
        if correct_answer_list and not user_answer_list:
            return 'No Output'
        elif correct_answer_list == user_answer_list:
            return 'Correct'
        else:
            return 'Wrong Answer'

# import platform
# platform.system()


def execute(cmd):
    os.system(cmd)


def run(command, input_file_path, output_file_path, time_limit_bound):
    cmd = command + "<" + input_file_path + ">" + output_file_path
    start_time = time.clock()
    signal = os.system("timeout -s SIGKILL -k %ds %ds %s" %
                       (time_limit_bound * 2, time_limit_bound, cmd))
    end_time = time.clock()
    if signal == 256:
        return ("Run Time Error", 0.0)
    elif signal == 35072:
        return ('Time Limit Exceeded', time_limit_bound)
    elif signal == 0:
        return ('Correct', end_time - start_time)


def compile(command):
    failure = subprocess.call(command, shell=True)
    if failure:
        return False
    return True


def judge(file_name, problem, language, submit, rejudge=False):
    if not os.path.exists(file_name):
        raise PermissionDenied
    without_extension = file_name
    try:
        index = without_extension[::-1].index('.')
        try:
            slash_index = without_extension[::-1].index('/')
            if index < slash_index:
                without_extension = without_extension[::-1][index+1:][::-1]
        except Exception:
            without_extension = without_extension[::-1][index+1:][::-1]
    except Exception:
        pass
    compile_command = language.compile_command
    run_command = language.run_command
    new_compile_command = convert_to_command(
        file_name=file_name, command=compile_command, filename_without_extension=without_extension)
    new_run_command = convert_to_command(
        file_name=file_name, command=run_command, filename_without_extension=without_extension)
    if language.name == 'Java':
        new_run_command = (new_run_command[::-1].replace('/', ' ', 1))[::-1]
    result = compile(command=new_compile_command)
    if not result:
        return 'Compiler Error'
    test_cases = [i for i in TestCase.objects.filter(
        problem=problem).order_by('name')]
    time_limit = float(problem.time_limit)

    submit_result = "Correct"
    for each in test_cases:
        input_file = each.input
        output_file = each.output
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        user_output_text_path = os.path.join(
            BASE_DIR, 'static/testcase_output.out')
        if rejudge:
            try:
                # for all except compiler error and run time error
                insert = TestcaseOutput.objects.get(
                    submit=submit, test_case=each)
            except TestcaseOutput.DoesNotExist:
                try:
                    user_output = File(open(user_output_text_path, 'r'))
                    insert = TestcaseOutput(
                        output_file=user_output, test_case=each, submit=submit)
                    insert.save()
                except IntegrityError:
                    pass
        else:
            try:
                user_output = File(open(user_output_text_path, 'r'))
                insert = TestcaseOutput(
                    output_file=user_output, test_case=each, submit=submit)
                insert.save()
            except IntegrityError:
                pass
        testcase_input_file_path = input_file.path
        user_output_file_path = insert.output_file.path
        testcase_output_file_path = output_file.path
        result, execute_time = run(command=new_run_command, input_file_path=testcase_input_file_path,
                                   output_file_path=user_output_file_path, time_limit_bound=time_limit)
        insert.execution_time = execute_time
        if result == "Run Time Error":
            insert.result = "Run Time Error"
            insert.save()
            return "Run Time Error"
        elif result == 'Time Limit Exceeded':
            insert.result = 'Time Limit Exceeded'
            insert.save()
            return 'Time Limit Exceeded'
        result = check_answer(correct_answer_file=testcase_output_file_path,
                              user_answer_file=user_output_file_path, error=problem.error)
        insert.result = result
        insert.save()
        if result == 'Correct':
            continue
        elif result == "Wrong Answer":
            submit_result = "Wrong Answer"
        else:
            return result
    # print(submit.id, submit_result)
    return submit_result


def read_source_code(files):
    files.open(mode='r')
    try:
        file_list = files.readlines()
    except UnicodeDecodeError:
        file_list = []
    submit_file = ''
    for i in file_list:
        submit_file += i
    files.close()
    return submit_file


def read_from_file(files):
    max_byte = 50
    files.open(mode='r')
    try:
        # file_list = files.readlines(max_byte)
        N = 100
        file_list = [line for line in [files.readline()
                                       for _ in range(N)] if len(line)]

    except UnicodeDecodeError:
        file_list = []
    submit_file = ''
    for i in file_list:
        submit_file += i
    files.seek(0, os.SEEK_END)
    file_size = files.tell()
    files.close()
    if file_size > max_byte:
        submit_file += "\n..."
    # print(files, file_list)
    return submit_file


def rank_update(submit):
    if not submit.user.role.short_name == "contestant":
        return
    if not submit.result:
        return
    if submit.submit_time < submit.contest.start_time:
        return
    if submit.submit_time >= submit.contest.end_time:
        return
    pro = submit.problem
    contest = submit.contest
    this_problem_prevous_correct_submit = Submit.objects.filter(
        contest=contest, problem=pro, result='Correct', submit_time__lte=submit.submit_time, user=submit.user).exclude(pk=submit.pk)
    if this_problem_prevous_correct_submit:
        return

    try:
        rank_cache = RankcacheJury.objects.get(
            user=submit.user, contest=contest)
    except RankcacheJury.DoesNotExist:
        rank_cache = RankcacheJury(user=submit.user, contest=contest)
        rank_cache.save()

    try:
        rank_cache_public = RankcachePublic.objects.get(
            user=submit.user, contest=contest)
    except RankcachePublic.DoesNotExist:
        rank_cache_public = RankcachePublic(user=submit.user, contest=contest)
        rank_cache_public.save()

    try:
        score_cache = ScorecacheJury.objects.get(
            rank_cache=rank_cache, problem=pro)
    except ScorecacheJury.DoesNotExist:
        score_cache = ScorecacheJury(rank_cache=rank_cache, problem=pro)
        score_cache.save()

    try:
        score_cache_public = ScorecachePublic.objects.get(
            rank_cache=rank_cache_public, problem=pro)
    except ScorecachePublic.DoesNotExist:
        score_cache_public = ScorecachePublic(
            rank_cache=rank_cache_public, problem=pro)
        score_cache_public.save()

    if score_cache.is_correct:
        return
    score_cache.submission += 1
    if submit.result == "Correct":
        score_cache.is_correct = True
        score_cache.correct_submit_time = submit.submit_time
    elif submit.result == "Compiler Error":
        pass
    else:
        score_cache.punish += 1
    score_cache.save()

    if submit.result == "Correct":
        punish_value, rating_correct_value, rating_punish_value = setting_values()
        rank_cache.point = (float(rank_cache.point) + float(pro.point))
        rank_cache.punish_time += punish_value * score_cache.punish + \
            time_gap(score_cache.correct_submit_time, contest.start_time)
        rank_cache.save()
        if contest.has_value:  # rating update
            user = submit.user
            user.rating += (rating_correct_value -
                            rating_punish_value * score_cache.punish)
            user.save()

    if contest.frozen_time and contest.unfrozen_time and contest.frozen_time <= submit.submit_time and submit.submit_time < contest.unfrozen_time:
        score_cache_public.submission += 1
        score_cache_public.pending += 1
        score_cache_public.save()
    else:
        rank_cache_public.point = rank_cache.point
        rank_cache_public.punish_time = rank_cache.punish_time
        rank_cache_public.save()

        score_cache_public.submission = score_cache.submission
        score_cache_public.punish = score_cache.punish
        score_cache_public.correct_submit_time = score_cache.correct_submit_time
        score_cache_public.is_correct = score_cache.is_correct
        score_cache_public.save()


@login_required
@contestant_auth
# @async_to_sync
def submit(request):
    refresh_contest_session_contestant(request)  # refersh the contest session
    current_contest_id = request.session.get('start_contest_contestant')
    problem_list = None
    all_current_contest_submits = []
    try:
        current_contest = Contest.objects.get(
            pk=current_contest_id, start_time__lte=timezone.now(), enable=True)
    except Contest.DoesNotExist:
        current_contest = None
    if current_contest:
        problem_list = current_contest.problem.all().order_by('short_name')
        if request.method == "POST":
            form = SubmitAnswer(request.POST, request.FILES)
            form.fields['problem'].queryset = problem_list
            if form.is_valid():
                post = form.save(commit=False)
                post.submit_time = timezone.now()
                post.user = request.user

                post.contest_id = current_contest_id
                post.submit_file = None
                post.save()
                post.submit_file = request.FILES.get('submit_file')
                post.save()

                # multiprocessing
                # pool = multiprocessing.Pool(processes=4)
                # pool.map(judge(file_name=post.submit_file.path, problem=post.problem, language=post.language, submit=post), request)
                
                ########################
                # TODO: convert the judge function to a function that takes a callback, the callback sets and saves the result to db and update ranklist
                # TODO: in the meanwhile redirect the user to submission page and show the progress as pending
                # TODO: when done the function will refresh the page to show the result ?? maybe add a notification like codeforces
                ########################

                result = judge(file_name=post.submit_file.path,
                               problem=post.problem, language=post.language, submit=post)
                post.result = result
                post.save()
                this_contest = post.contest
                this_contest.last_update = timezone.now()
                this_contest.save()

                rank_update(post)
                # output_files = TestcaseOutput.objects.filter(submit = post)
                # for i in output_files:
                #     if i.result == "Correct":
                #         continue
                #     else:
                #         if i.output_file.size > 2 * i.test_case.output.size:
                #             os.system('rm '+i.output_file.path)
                #             os.system('touch '+i.output_file.path)
                # if this_contest.has_value:
                #     give_score(post, request)
                return redirect('submit')
        else:
            form = SubmitAnswer()
            form.fields['problem'].queryset = problem_list
    else:
        form = None

    q = Q(problem=None)
    if current_contest:
        for pro in current_contest.problem.all():
            q = q | Q(problem=pro)
        all_current_contest_submits = Submit.objects.filter(
            q, contest_id=current_contest_id, user=request.user).order_by('submit_time').reverse()
        start_time = current_contest.start_time
        for i in all_current_contest_submits:
            if i.submit_time > current_contest.end_time:
                i.result = 'Too Late'
            i.contest_time = i.submit_time - start_time
            i.source_code = read_source_code(i.submit_file)
            i.language_mode = i.language.editor_mode

        a = [i for i in all_current_contest_submits]
        ls = []
        for i in a:
            ls.append((i.pk, str(i.submit_file)))
    else:
        all_current_contest_submits = None
        ls = []
    qs_json = json.dumps(ls)

    try:
        active_contest = Contest.objects.get(pk=request.session.get(
            'active_contest_contestant'), active_time__lte=timezone.now(), enable=True)
        contest_title = active_contest.title
        start_time = active_contest.start_time
    except Contest.DoesNotExist:
        contest_title = None
        start_time = None

    return render(request, 'submit.html',
                  {'form': form, 'all_current_contest_submits': all_current_contest_submits,
                   'current_contest': current_contest, 'qs_json': qs_json,
                   'contest_title': contest_title, 'start_time': start_time, 'submit': 'hover'
                   }
                  )


def scoreboard_summary(contest, scoreboard_type):
    total_problems = contest.problem.all().order_by('short_name')
    q = Q(problem=None)
    for pro in contest.problem.all():
        q = q | Q(problem=pro)
    problem_summary_dict = {i: [0, 0] for i in total_problems}

    if scoreboard_type == "public":
        user_rank_cache = RankcachePublic.objects.filter(contest=contest)
        user_score_cache = ScorecachePublic.objects.filter(
            q, rank_cache__contest=contest)
    else:
        user_rank_cache = RankcacheJury.objects.filter(contest=contest)
        user_score_cache = ScorecacheJury.objects.filter(
            q, rank_cache__contest=contest)
    total_user = 0
    total_point = 0
    total_time = 0
    for rank in user_rank_cache:
        total_user += 1
        total_point += rank.point
        total_time += rank.punish_time

    for score in user_score_cache:
        problem_summary_dict[score.problem][0] += score.submission
        if score.is_correct:
            problem_summary_dict[score.problem][1] += 1

    if total_point == int(total_point):
        total_point = int(total_point)
    summary = [total_user, 'summary', total_point, total_time]
    for pro in total_problems:
        this_problem = "%d/%d" % tuple(problem_summary_dict[pro])
        summary.append(this_problem)
    return summary


def first_solver(score_cache, problem_list, contest_start_time):
    first_solver_list = []
    for problem in problem_list:
        this_problem_submit = score_cache.filter(
            is_correct=True, problem=problem).order_by('correct_submit_time')
        this_problem_first_solver = []
        if this_problem_submit:
            first_time = time_gap(
                this_problem_submit[0].correct_submit_time, contest_start_time)
            for score in this_problem_submit:
                time = time_gap(score.correct_submit_time, contest_start_time)
                if time > first_time:
                    break
                else:
                    first_solver_list.append((score.rank_cache.user, problem))
    return first_solver_list


def calculate_problem_score_public(score_cache_public, total_problems, contest_start_time, first_solver_list):
    score_vs_problem = dict()
    for score in score_cache_public:
        pro = score.problem
        if score.is_correct:
            time = time_gap(score.correct_submit_time, contest_start_time)
            if (score.rank_cache.user, pro) in first_solver_list:
                score_vs_problem[pro] = (score.submission, time, "#26ac0c")
            else:
                score_vs_problem[pro] = (score.submission, time, "#2ef507")
        elif score.pending:
            if score.punish:
                score_vs_problem[pro] = (
                    "%d+%d" % (score.punish, score.pending), -1, "#007F7F")
            else:
                score_vs_problem[pro] = (score.pending, -1, "#007F7F")
        else:
            score_vs_problem[pro] = (score.submission, -1, "#F67B51")
    problem_display = []
    for pro in total_problems:
        if pro in score_vs_problem:
            problem_display.append(score_vs_problem[pro])
        else:
            problem_display.append((0, -1, "#ffffff"))
    return problem_display


def calculate_problem_score_jury(score_cache_jury, total_problems, contest_start_time, first_solver_list):
    score_vs_problem = dict()
    for score in score_cache_jury:
        pro = score.problem
        if score.is_correct:
            time = time_gap(score.correct_submit_time, contest_start_time)
            if (score.rank_cache.user, pro) in first_solver_list:
                score_vs_problem[pro] = (
                    score.submission, time, "#26ac0c", pro.id)
            else:
                score_vs_problem[pro] = (
                    score.submission, time, "#2ef507", pro.id)
        elif score.punish:
            score_vs_problem[pro] = (score.submission, -1, "#F67B51", pro.id)
    problem_display = []
    for pro in total_problems:
        if pro in score_vs_problem:
            problem_display.append(score_vs_problem[pro])
        else:
            problem_display.append((0, -1, "#ffffff", pro.id))
    return problem_display


def last_submit(score_cache, contest_end_time, contest_start_time):
    last = contest_start_time
    is_correct_submit = False
    for submit in score_cache:
        if submit.is_correct:
            if last < submit.correct_submit_time:
                last = submit.correct_submit_time
                is_correct_submit = True
    if is_correct_submit:
        return time_gap(last, contest_start_time)
    else:
        return time_gap(contest_end_time, contest_start_time)


def create_rank(table):
    for users in table:
        users[0] = -users[0]
    table.sort()
    for users in table:
        users[0] = -users[0]
    if table:
        table[0].append(1)
    for i in range(1, len(table)):
        if table[i][:3] == table[i-1][:3]:
            table[i].append('')
        else:
            table[i].append(i+1)
    return table


def calculate_scoreboard(request, contest_id, scoreboard_type):
    current_contest = Contest.objects.get(pk=contest_id)
    contest_start_time = current_contest.start_time
    total_users = current_contest.user.filter(role__short_name="contestant")
    total_problems = current_contest.problem.all().order_by('short_name')
    q = Q(problem=None)
    for pro in current_contest.problem.all():
        q = q | Q(problem=pro)

    now = timezone.now()
    if scoreboard_type == "public":
        rank_cache = RankcachePublic.objects.filter(contest=current_contest)
        score_cache = ScorecachePublic.objects.filter(
            q, rank_cache__contest=current_contest)
    else:
        rank_cache = RankcacheJury.objects.filter(contest=current_contest)
        score_cache = ScorecacheJury.objects.filter(
            q, rank_cache__contest=current_contest)

    first_solver_list = first_solver(
        score_cache, total_problems, contest_start_time)
    display = []
    for users in total_users:
        user_score_cache = score_cache.filter(rank_cache__user=users)
        if scoreboard_type == "public":
            problem_display = calculate_problem_score_public(
                user_score_cache, total_problems, contest_start_time, first_solver_list)
        else:
            problem_display = calculate_problem_score_jury(
                user_score_cache, total_problems, contest_start_time, first_solver_list)

        try:
            user_rank_cache = rank_cache.get(user=users)
            user_point = float(user_rank_cache.point)
            punish_time = user_rank_cache.punish_time
        except:
            continue

        if user_point == int(user_point):
            user_point = int(user_point)
        last_submit_time = last_submit(
            user_score_cache, current_contest.end_time, contest_start_time)
        flag = users.campus.flag()
        this_user_row = [user_point, punish_time, last_submit_time,
                         users.name, users.id, users.campus.name, flag, problem_display]
        display.append(this_user_row)
    rank = create_rank(display)
    return rank


# @login_required
# @contestant_auth
def public_scoreboard(request):
    now = timezone.now()
    if request.user.is_authenticated:  # the user is contestant
        # refresh contestant contest session
        refresh_contest_session_contestant(request)
        contest_id = request.session.get('start_contest_contestant')
        base_page = "contestant_base_site.html"
        role = "contestant"
    else:
        # refresh public contest session
        refresh_contest_session_public(request)
        contest_id = request.session.get('start_contest_public')
        base_page = "public_scoreboard_base_site.html"
        role = "public"
    frozen = None
    if contest_id:
        current_contest = Contest.objects.get(pk=contest_id)

        unfrozen_time = current_contest.unfrozen_time
        if not unfrozen_time:
            unfrozen_time = current_contest.end_time
        if current_contest.last_update < unfrozen_time and now >= unfrozen_time:
            current_contest.last_update = unfrozen_time
            rank_update_unfrozen(current_contest)
            current_contest.save()
        # if current_contest.last_update < current_contest.start_time and now >= current_contest.start_time:
        #     current_contest.last_update = current_contest.start_time
        #     current_contest.save()
        if current_contest.frozen_time and now >= current_contest.frozen_time and now < unfrozen_time:
            frozen = (current_contest.frozen_time, unfrozen_time)
        else:
            frozen = None
        total_problems = current_contest.problem.all().order_by('short_name')
        last_update = str(current_contest.last_update)
        scoreboard_in_session = request.session.get(
            'public_scoreboard_contest_id_' + str(contest_id))
        if now < current_contest.start_time:
            scoreboard = None
        elif scoreboard_in_session and scoreboard_in_session['last_update'] == last_update:
            scoreboard = scoreboard_in_session['scoreboard']
        else:
            scoreboard_public = calculate_scoreboard(
                request, contest_id, "public")
            summary = scoreboard_summary(current_contest, "public")
            scoreboard = {
                'scoreboard_public': scoreboard_public,
                'summary': summary,
            }
            request.session['public_scoreboard_contest_id_' + str(contest_id)] = {
                'last_update': last_update, 'scoreboard': scoreboard, 'contest_id': contest_id}

    else:
        scoreboard = total_problems = contest_title = current_contest = None

    if role == "contestant":
        try:
            active_contest = Contest.objects.get(pk=request.session.get(
                'active_contest_contestant'), active_time__lte=timezone.now(), enable=True)
            contest_title = active_contest.title
            start_time = active_contest.start_time
        except Contest.DoesNotExist:
            contest_title = None
            start_time = None
    else:
        try:
            active_contest = Contest.objects.get(pk=request.session.get(
                'active_contest_public'), active_time__lte=timezone.now(), enable=True)
            contest_title = active_contest.title
            start_time = active_contest.start_time
        except Contest.DoesNotExist:
            contest_title = None
            start_time = None

    context = {
        'scoreboard': scoreboard,
        'total_problems': total_problems,
        'contest': current_contest,
        'frozen': frozen,
        'contest_title': contest_title,
        'start_time': start_time,
        'base_page': base_page,
        'scor': 'hover',
        'role': role,
    }
    return render(request, 'public_scoreboard.html', context)


# @login_required
# @contestant_auth
def public_scoreboard_refresh(request):
    
    now = timezone.now()
    if request.user.is_authenticated:  # the user is contestant
        refresh_contest_session_contestant(request)
        contest_id = request.session.get('start_contest_contestant')
    else:
        contest_id = request.session.get('start_contest_public')
        refresh_contest_session_public(request)
    frozen = None
    if contest_id:
        current_contest = Contest.objects.get(pk=contest_id)

        unfrozen_time = current_contest.unfrozen_time
        if not unfrozen_time:
            unfrozen_time = current_contest.end_time
        if current_contest.last_update < unfrozen_time and now >= unfrozen_time:
            current_contest.last_update = unfrozen_time
            rank_update_unfrozen(current_contest)
            current_contest.save()
        # if current_contest.last_update < current_contest.start_time and now >= current_contest.start_time:
        #     current_contest.last_update = current_contest.start_time
        #     current_contest.save()
        if current_contest.frozen_time and now >= current_contest.frozen_time and now < unfrozen_time:
            frozen = (current_contest.frozen_time, unfrozen_time)
        else:
            frozen = None
        total_problems = current_contest.problem.all().order_by('short_name')
        last_update = str(current_contest.last_update)
        scoreboard_in_session = request.session.get(
            'public_scoreboard_contest_id_' + str(contest_id))
        if now < current_contest.start_time:
            scoreboard = None
        elif scoreboard_in_session and scoreboard_in_session['last_update'] == last_update:
            scoreboard = scoreboard_in_session['scoreboard']
        else:
            scoreboard_public = calculate_scoreboard(
                request, contest_id, "public")
            summary = scoreboard_summary(current_contest, "public")
            scoreboard = {
                'scoreboard_public': scoreboard_public,
                'summary': summary,
            }
            request.session['public_scoreboard_contest_id_' + str(contest_id)] = {
                'last_update': last_update, 'scoreboard': scoreboard, 'contest_id': contest_id}

    else:
        scoreboard = total_problems = current_contest = None

    context = {
        'scoreboard': scoreboard, 'total_problems': total_problems, 'contest': current_contest,
        'frozen': frozen, 'scor': 'hover'
    }
    return render(request, 'public_scoreboard_refresh.html', context)


@login_required
@contestant_auth
def ajax_get_language_list(request):
    active_contest_id = request.session.get('active_contest_contestant')
    try:
        contest = Contest.objects.get(id=active_contest_id)
    except Contest.DoesNotExist:
        contest = None
    language_list = [(lang.id, lang.extension)
                     for lang in Language.objects.all().order_by('name').reverse()]
    problem_list = [(pro.id, pro.title.lower(), pro.short_name.lower())
                    for pro in contest.problem.all()]
    response_data = {"language_list": language_list,
                     "problem_list": problem_list}
    return JsonResponse(response_data, content_type="application/json")


@login_required
@admin_or_jury_auth
def jury_scoreboard(request):
    refresh_contest_session_admin(request)
    now = timezone.now()
    contest_id = request.session.get('start_contest_admin')
    frozen = None
    if contest_id:
        current_contest = Contest.objects.get(pk=contest_id)

        total_problems = current_contest.problem.all().order_by('short_name')
        last_update = str(current_contest.last_update)
        scoreboard_in_session = request.session.get(
            'jury_scoreboard_contest_id_' + str(contest_id))
        if now < current_contest.start_time:
            scoreboard = None
        elif scoreboard_in_session and scoreboard_in_session['last_update'] == last_update:
            scoreboard = scoreboard_in_session['scoreboard']
        else:
            scoreboard_jury = calculate_scoreboard(request, contest_id, "jury")
            summary = scoreboard_summary(current_contest, "jury")
            scoreboard = {
                'scoreboard_jury': scoreboard_jury,
                'summary': summary,
            }
            request.session['jury_scoreboard_contest_id_' + str(contest_id)] = {
                'last_update': last_update, 'scoreboard': scoreboard, 'contest_id': contest_id}
    else:
        scoreboard = total_problems = contest_title = current_contest = None

    try:
        active_contest = Contest.objects.get(pk=request.session.get(
            'active_contest_admin'), active_time__lte=timezone.now(), enable=True)
        contest_title = active_contest.title
        start_time = active_contest.start_time
    except Contest.DoesNotExist:
        contest_title = None
        start_time = None
    base_page = check_base_site(request)

    context = {
        'scoreboard': scoreboard,
        'total_problems': total_problems,
        'contest': current_contest,
        'contest_title': contest_title,
        'start_time': start_time,
        "base_page": base_page,
        'scor': 'hover'
    }
    return render(request, 'jury_scoreboard.html', context)


@login_required
@admin_or_jury_auth
def jury_scoreboard_refresh(request):
    refresh_contest_session_admin(request)
    now = timezone.now()
    contest_id = request.session.get('start_contest_admin')
    frozen = None
    update = False
    if contest_id:
        current_contest = Contest.objects.get(pk=contest_id)

        total_problems = current_contest.problem.all().order_by('short_name')
        last_update = str(current_contest.last_update)
        scoreboard_in_session = request.session.get(
            'jury_scoreboard_contest_id_' + str(contest_id))
        if now < current_contest.start_time:
            scoreboard = None
        elif scoreboard_in_session and scoreboard_in_session['last_update'] == last_update:
            scoreboard = scoreboard_in_session['scoreboard']

        else:
            update = True
            scoreboard_jury = calculate_scoreboard(request, contest_id, "jury")
            summary = scoreboard_summary(current_contest, "jury")
            scoreboard = {
                'scoreboard_jury': scoreboard_jury,
                'summary': summary,
            }
            request.session['jury_scoreboard_contest_id_' + str(contest_id)] = {
                'last_update': last_update, 'scoreboard': scoreboard, 'contest_id': contest_id}
    else:
        scoreboard = total_problems = contest_title = current_contest = None

    if update:
        return render(request, 'jury_scoreboard_refresh.html', {'scoreboard': scoreboard, 'total_problems': total_problems, 'contest': current_contest, 'scor': 'hover'})
    else:
        return HttpResponse('')
    # if update:
    #     new_scoreboard  = render(request, 'jury_scoreboard_refresh.html', {'scoreboard': scoreboard, 'total_problems': total_problems, 'contest': current_contest, 'scor': 'hover'})
    # else:
    #     new_scoreboard = None
    # response_data = {"update": update, "scoreboard": new_scoreboard}
    # return JsonResponse(response_data, content_type="application/json")


@login_required
@admin_or_jury_auth
def deactivate_contest_scoreboard(request, contest_id):
    refresh_contest_session_admin(request)
    now = timezone.now()
    current_contest = Contest.objects.get(pk=contest_id)
    total_problems = current_contest.problem.all().order_by('short_name')
    scoreboard_jury = calculate_scoreboard(request, contest_id, "jury")
    summary = scoreboard_summary(current_contest, "jury")
    scoreboard = {
        'scoreboard_jury': scoreboard_jury,
        'summary': summary,
    }
    base_page = check_base_site(request)
    context = {'scoreboard': scoreboard, 'total_problems': total_problems,
               'contest': current_contest, 'base_page': base_page, 'scor': 'hover'}
    return render(request, 'view_deactivate_contest_scoreboard.html', context)


@login_required
@admin_or_jury_auth
def view_submit_contest_select(request):
    now = timezone.now()
    refresh_contest_session_admin(request)  # refersh the contest session
    all_contest = Contest.objects.filter(
        start_time__lte=now).order_by("start_time").reverse()
    for contest in all_contest:
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
    base_page = check_base_site(request)
    context = {
        'all_contest': all_contest,
        'base_page': base_page,
        'submit': 'hover'
    }
    return render(request, 'view_submit_select_contest.html', context)


@login_required
@admin_jury_auth_and_contest_exist
def view_submissions(request, contest_id):
    refresh_contest_session_admin(request)  # refersh the contest session
    contest = Contest.objects.get(pk=contest_id)

    submission_list = Submit.objects.filter(
        contest=contest).order_by('submit_time').reverse()
    base_page = check_base_site(request)
    all_problems = set()
    for submit in submission_list:
        pro = (submit.problem.id, submit.problem.title)
        all_problems.add(pro)
    all_problems = sorted(all_problems, key=lambda x: x[1].lower())
    start_time = contest.start_time
    for i in submission_list:
        i.contest_time = i.submit_time - start_time
    context = {'submission_list': submission_list, "contest_title": contest.title, 'base_page': base_page,
               'all_problems': all_problems, 'contest_id': contest_id, 'submit': 'hover'
               }
    return render(request, 'view_submission.html', context)


@login_required
@admin_or_jury_auth
def view_submission_filter(request):
    refresh_contest_session_admin(request)  # refersh the contest session
    problem_id = int(request.GET.get('problem_id'))
    contest_id = int(request.GET.get('contest_id'))
    try:
        problem_title = Problem.objects.get(pk=problem_id).title
    except Problem.DoesNotExist:
        problem_title = None
    if problem_id == 0:
        all_submissions = Submit.objects.filter(
            contest_id=contest_id).order_by('submit_time').reverse()
        problem_title = "All problems"
    else:
        all_submissions = Submit.objects.filter(
            contest_id=contest_id, problem_id=problem_id).order_by('submit_time').reverse()
    contest = Contest.objects.get(pk=contest_id)
    start_time = contest.start_time
    for i in all_submissions:
        i.contest_time = i.submit_time - start_time
    return render(request, 'view_submission_filter.html', {'submission_list': all_submissions, 'problem_title': problem_title, 'submit': 'hover'})


@login_required
@admin_jury_auth_and_submit_exist
def submission_detail(request, submit_id):
    refresh_contest_session_admin(request)  # refersh the contest session
    submit = Submit.objects.get(pk=submit_id)
    submit_contest_time = submit.submit_time - submit.contest.start_time

    answer_file = submit.submit_file
    submit_file = read_source_code(answer_file)
    language_mode = submit.language.editor_mode
    error = submit.problem.error
    file_name = answer_file.name
    try:
        index = file_name[::-1].index('/')
        file_name = file_name[::-1][:index][::-1]
    except Exception:
        pass
    # detail about the test cases
    submit_detail = []

    all_user_testcases = TestcaseOutput.objects.filter(
        submit=submit).order_by('test_case')
    run_testcases = [i.test_case for i in all_user_testcases]
    testcase_correct_answer = TestCase.objects.filter(
        problem=submit.problem).order_by('name')
    all_user_answers = {}
    all_correct_answers = {}
    for i in all_user_testcases:
        user_answer_file = i.output_file
        all_user_answers[i.test_case.id] = read_from_file(
            user_answer_file).strip().split('\n')
    for j in testcase_correct_answer:
        correct_answer_file = j.output
        all_correct_answers[j.id] = read_from_file(
            correct_answer_file).strip().split('\n')
    for i in all_user_testcases:
        execution_time = float(i.execution_time)
        if not execution_time == 0:
            execution_time = ('%f' % execution_time)
        testcase_id = i.test_case.id
        result = i.result

        url = i.test_case.input.url
        file_path = url
        try:
            index = file_path[::-1].index('/')
            file_path = file_path[::-1][:index][::-1]
        except Exception:
            pass
        testcase_input_file = (url, file_path)

        url = i.test_case.output.url
        file_path = url
        try:
            index = file_path[::-1].index('/')
            file_path = file_path[::-1][:index][::-1]
        except Exception:
            pass
        testcase_output_file = (url, file_path)

        url = TestcaseOutput.objects.get(
            test_case=i.test_case, submit=submit).output_file.url
        file_path = url
        try:
            index = file_path[::-1].index('/')
            file_path = file_path[::-1][:index][::-1]
        except Exception:
            pass
        user_output_file = (url, file_path)

        answer_compare = []
        x = all_correct_answers[testcase_id]
        y = all_user_answers[testcase_id]
        for k in range(min(len(x), len(y))):
            correct_line = x[k].split()
            user_line = y[k].split()
            if len(correct_line) != len(user_line):
                answer_compare.append((x[k], y[k], 'Wrong Answer'))
                continue
            for a, b in zip(correct_line, user_line):
                if a == b:
                    continue
                try:
                    a = float(a)
                    b = float(b)
                except ValueError:
                    answer_compare.append((x[k], y[k], 'Wrong Answer'))
                    break
                if math.fabs(a - b) > error:
                    answer_compare.append((x[k], y[k], 'Wrong Answer'))
                    break
            else:
                answer_compare.append((x[k], y[k], 'Correct'))
        for k in range(len(x), len(y)):
            answer_compare.append(('', y[k], 'Wrong Answer'))
        for k in range(len(y), len(x)):
            answer_compare.append((x[k], '', 'Wrong Answer'))
        submit_detail.append((testcase_id, result, answer_compare, testcase_input_file,
                              testcase_output_file, user_output_file, execution_time))
    for i in testcase_correct_answer:
        if i in run_testcases:
            continue
        else:
            submit_detail.append(
                (i.id, "Not Run", [], (None, None), (None, None), (None, None), 0))
    base_page = check_base_site(request)
    context = {'submit': submit, 'submit_file': submit_file, 'language_mode': language_mode, 'file_name': file_name,
               'submit_detail': submit_detail, 'submit_contest_time': submit_contest_time, 'base_page': base_page}
    return render(request, 'submission_detail.html', context)


@login_required
@admin_or_jury_auth
def rating(request):
    user_rating = User.objects.filter(
        role__short_name='contestant', rating__gt=0).order_by('rating').reverse()

    user_rank = [[rank + 1, row] for rank, row in enumerate(user_rating)]
    for i in range(1, len(user_rank)):
        if user_rank[i-1][1].rating == user_rank[i][1].rating:
            user_rank[i][0] = ''

    base_page = check_base_site(request)
    context = {
        "user_rank": user_rank,
        "base_page": base_page,
        'rating': 'hover'
    }
    return render(request, 'rating.html', context)


@login_required
@admin_or_jury_auth
def specific_problem_submission(request):
    problem_id = request.GET.get('problem_id')
    user_id = request.GET.get('user_id')
    contest_id = request.GET.get('contest_id')
    refresh_contest_session_admin(request)  # refersh the contest session
    current_contest = Contest.objects.get(pk=contest_id)
    this_problem_and_user_submissions = Submit.objects.filter(contest_id=contest_id, problem_id=problem_id, user_id=user_id,
                                                              submit_time__gte=current_contest.start_time, submit_time__lte=current_contest.end_time).order_by('submit_time')
    correct = False
    specific_submissions = list()
    for submissions in this_problem_and_user_submissions:
        if correct:
            break
        elif submissions.result == 'Correct':
            correct = True
            specific_submissions.append(submissions)
        else:
            specific_submissions.append(submissions)

    start_time = current_contest.start_time
    for i in specific_submissions:
        i.contest_time = i.submit_time - start_time

    base_page = check_base_site(request)

    return render(request, 'specific_problem_submission.html', {'submit': specific_submissions, 'contest_id': contest_id, 'base_page': base_page})


@login_required
@admin_auth
def rejudge_contest_select(request):
    now = timezone.now()
    refresh_contest_session_admin(request)  # refersh the contest session
    all_contest = Contest.objects.filter(
        start_time__lte=now).order_by("start_time").reverse()

    for contest in all_contest:
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
    context = {'all_contest': all_contest, 'rejudge': 'hover'}
    return render(request, 'rejudge_select_contest.html', context)


@login_required
@admin_auth_and_contest_exist
def rejudge_submission_list(request, contest_id):
    refresh_contest_session_admin(request)  # refersh the contest session
    contest = Contest.objects.get(pk=contest_id)

    submission_list = Submit.objects.filter(
        contest=contest).order_by('submit_time').reverse()
    all_problems = set()

    start_time = contest.start_time
    for i in submission_list:
        i.contest_time = i.submit_time - start_time
    for submit in submission_list:
        pro = (submit.problem.id, submit.problem.title)
        all_problems.add(pro)
    all_problems = sorted(all_problems, key=lambda x: x[1].lower())
    context = {'submission_list': submission_list, "contest_title": contest.title,
               'all_problems': all_problems, 'contest_id': contest.pk, 'rejudge': 'hover'}
    return render(request, 'rejudge_submission_list.html', context)


@login_required
@admin_auth
def rejudge_submission_filter(request):
    refresh_contest_session_admin(request)  # refersh the contest session
    problem_id = int(request.GET.get('problem_id'))
    contest_id = int(request.GET.get('contest_id'))

    try:
        contest = Contest.objects.get(pk=contest_id)
    except Contest.DoesNotExist:
        return redirect('homepage')
    try:
        problem_title = Problem.objects.get(pk=problem_id).title
    except Problem.DoesNotExist:
        problem_title = None
    if problem_id == 0:
        all_submissions = Submit.objects.filter(
            contest_id=contest_id).order_by('submit_time').reverse()
        problem_title = "All problems"
    else:
        all_submissions = Submit.objects.filter(
            contest_id=contest_id, problem_id=problem_id).order_by('submit_time').reverse()

    start_time = contest.start_time
    for i in all_submissions:
        i.contest_time = i.submit_time - start_time

    return render(request, 'rejudge_filter.html', {'submission_list': all_submissions, 'problem_title': problem_title, 'rejudge': 'hover'})


def update_score_and_rank(submit):
    point = submit.problem.point
    contest = submit.contest

    rank_cache_jury = RankcacheJury.objects.get(
        user=submit.user, contest=contest)
    rank_cache_public = RankcachePublic.objects.get(
        user=submit.user, contest=contest)
    try:
        score_cache_jury = ScorecacheJury.objects.get(
            rank_cache=rank_cache_jury, problem=submit.problem)
    except ScorecacheJury.DoesNotExist:
        score_cache_jury = ScorecacheJury(
            rank_cache=rank_cache_jury, problem=submit.problem)
        score_cache_jury.save()

    try:
        score_cache_public = ScorecachePublic.objects.get(
            rank_cache=rank_cache_public, problem=submit.problem)
    except ScorecachePublic.DoesNotExist:
        score_cache_public = ScorecachePublic(
            rank_cache=rank_cache_public, problem=submit.problem)
        score_cache_public.save()

    try:
        punish_value = Setting.objects.get(name="punish time").value
    except Setting.DoesNotExist:
        punish_value = 20

    if score_cache_jury.is_correct:
        rank_cache_jury.point -= point
        rank_cache_jury.punish_time -= (punish_value * score_cache_jury.punish + time_gap(
            score_cache_jury.correct_submit_time, contest.start_time))
        rank_cache_jury.save()
        if contest.has_value:  # rating update
            user = submit.user
            user.rating -= (20 - 1 * score_cache_jury.punish)
            user.save()

    score_cache_jury.is_correct = False
    score_cache_jury.punish = 0
    score_cache_jury.submission = 0
    score_cache_jury.correct_submit_time = None
    score_cache_jury.save()

    if score_cache_public.is_correct:
        rank_cache_public.point -= point
        rank_cache_public.punish_time -= (punish_value * score_cache_public.punish + time_gap(
            score_cache_public.correct_submit_time, contest.start_time))
        rank_cache_public.save()

    score_cache_public.is_correct = False
    score_cache_public.punish = 0
    score_cache_public.submission = 0
    score_cache_public.correct_submit_time = None
    score_cache_public.pending = 0
    score_cache_public.save()

    all_submit = Submit.objects.filter(user=submit.user, problem=submit.problem, contest=contest, submit_time__gte=contest.start_time,
                                       submit_time__lte=contest.end_time).order_by('submit_time')
    for sub in all_submit:
        score_cache_jury.submission += 1
        if sub.result == "Correct":
            score_cache_jury.correct_submit_time = sub.submit_time
            score_cache_jury.is_correct = True
            rank_cache_jury.point += point
            rank_cache_jury.punish_time += (punish_value * score_cache_jury.punish + time_gap(
                score_cache_jury.correct_submit_time, contest.start_time))
            rank_cache_jury.save()
            break
        elif not sub.result == "Compiler Error":
            score_cache_jury.punish += 1
    score_cache_jury.save()

    for sub in all_submit:
        if contest.frozen_time and contest.unfrozen_time and contest.frozen_time <= sub.submit_time and sub.submit_time < contest.unfrozen_time:
            score_cache_public.submission += 1
            score_cache_public.pending += 1
            score_cache_public.save()
        else:
            rank_cache_public.point = rank_cache_jury.point
            rank_cache_public.punish_time = rank_cache_jury.punish_time
            rank_cache_public.save()

            score_cache_public.submission = score_cache_jury.submission
            score_cache_public.punish = score_cache_jury.punish
            score_cache_public.correct_submit_time = score_cache_jury.correct_submit_time
            score_cache_public.is_correct = score_cache_jury.is_correct
            score_cache_public.save()

    if contest.has_value and score_cache_jury.is_correct:  # rating update
        user = submit.user
        user.rating += (20 - 1 * score_cache_jury.punish)
        user.save()


@login_required
@admin_auth
def ajax_rejudge(request):
    refresh_contest_session_admin(request)  # refersh the contest session
    total_submits = request.GET.getlist('total_submit[]')
    contest_id = request.GET.get('contest_id')
    contest = Contest.objects.get(pk=contest_id)
    rejudge_submits = [int(i) for i in total_submits]
    result_dict = {}
    for submit_id in rejudge_submits:
        try:
            submit = Submit.objects.get(pk=submit_id)
            try:
                result = judge(file_name=submit.submit_file.path, problem=submit.problem,
                       language=submit.language, submit=submit, rejudge=True)
                submit.result = result
                submit.save()
                update_score_and_rank(submit)
            except ValueError:
                result = "file not found"
        except Submit.DoesNotExist:
            result = "not submitted"

        # output_files = TestcaseOutput.objects.filter(submit = submit)
        # for i in output_files:
        #     if i.result == "Correct":
        #         continue
        #     else:
        #         if i.output_file.size > 2 * i.test_case.output.size:
        #             os.system('rm '+i.output_file.path)
        #             os.system('touch '+i.output_file.path)
        result_dict[submit_id] = submit.result
    contest.last_update = timezone.now()
    contest.save()
    response_data = {'result': result_dict}
    return JsonResponse(response_data, content_type="application/json")


@login_required
@admin_auth_and_submit_exist
def single_rejudge(request, submit_id):
    refresh_contest_session_admin(request)  # refersh the contest session
    single_submit = Submit.objects.get(pk=submit_id)
    single_submit.contest_time = single_submit.submit_time - \
        single_submit.contest.start_time
    submit = [single_submit]

    return render(request, 'single_user_rejudge.html', {'submit': submit, 'contest_id': single_submit.contest.pk, 'rejudge': 'hover'})


@login_required
@admin_auth
def multi_rejudge(request, problem_id, contest_id, user_id):
    refresh_contest_session_admin(request)  # refersh the contest session
    # contest_id = request.session.get('start_contest_admin')  # ???
    current_contest = Contest.objects.get(pk=contest_id)
    submit = Submit.objects.filter(contest_id=contest_id, problem_id=problem_id, user_id=user_id,
                                   submit_time__gte=current_contest.start_time, submit_time__lte=current_contest.end_time).order_by('submit_time')
    if not submit:
        return redirect('homepage')
    specific_submissions = list()
    for i in submit:
        if i.result == 'Correct':
            specific_submissions.append(i)
            break
        else:
            specific_submissions.append(i)
    start_time = current_contest.start_time
    for i in specific_submissions:
        i.contest_time = i.submit_time - start_time

    return render(request, 'single_user_rejudge.html', {'submit': specific_submissions, 'contest_id': specific_submissions[0].contest.pk, 'rejudge': 'hover'})
