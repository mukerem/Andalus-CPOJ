from django.shortcuts import render, render_to_response, redirect
from django.http import JsonResponse
from problem.models import Problem
from public.forms import SubmitAnswer, SubmitSpecificProblem
from competitive.models import Submit, Language, TestcaseOutput, TestCase
from competitive.views import read_source_code, read_from_file
from django.contrib.auth.decorators import login_required
from authentication.decorators import public_auth, public_auth_and_problem_exist, admin_auth, \
        admin_jury_auth_and_submit_exist, admin_or_jury_auth, admin_jury_auth_and_contest_exist, \
        admin_auth_and_submit_exist
from django.utils import timezone
from competitive.views import judge
from public.models import Statistics
from django.db import IntegrityError
from authentication.models import User
from authentication.views import check_base_site
import math
# Create your views here.


def difficulty(statistics):
    try:
        ratio = 8.9 * \
            float(statistics.accurate_submissions) / \
            statistics.total_submissions
    except ZeroDivisionError:
        ratio = 8.9
    difficulty = round(9.9 - ratio, 1)
    return difficulty


@login_required
@public_auth
def public_problem_list(request):
    # problem_list = Problem.objects.filter(is_public=True).order_by('title')
    problem_list = Statistics.objects.filter(is_active=True).order_by("problem__title")
    for stats in problem_list:
        stats.difficulty = difficulty(stats)
        try:
            stats.submissions_ratio = 100 * stats.accurate_submissions // stats.total_submissions
        except ZeroDivisionError:
            stats.submissions_ratio = 100

        try:
            stats.user_ratio = 100 * stats.accurate_users // stats.total_users
        except ZeroDivisionError:
            stats.user_ratio = 100
    for stat in problem_list:
        submit = Submit.objects.filter(user=request.user, problem=stat.problem)
        if submit.filter(result="Correct"):
            stat.status = "Solved"
        elif submit:
            stat.status = "Not Solved"
        else:
            stat.status = "Not Try"
    return render(request, 'problem_list.html', {'problem_list': problem_list})


def update_statistics(submit):
    try:
        stat = Statistics.objects.get(problem=submit.problem)
        stat.total_submissions += 1
        if submit.result == "Correct":
            stat.accurate_submissions += 1
        previous = Submit.objects.filter(user=submit.user, problem=submit.problem).exclude(pk=submit.pk)
        if not previous:
            stat.total_users += 1
            if submit.result == "Correct":
                stat.accurate_users += 1
        else:
            if submit.result == "Correct":
            	if not previous.filter(result="Correct"):
            		stat.accurate_users += 1
                # correct  = False
                # for sub in previous:
                #     if sub.result == "Correct":
                #         correct = True
                #         break
                # if not correct:
                    # stat.accurate_users += 1
        stat.save()
    except Statistics.DoesNotExist:
        stat = Statistics(problem=submit.problem)
        stat.save()


@login_required
@public_auth
def public_submit(request):
    problem_list = Problem.objects.filter(is_public=True).order_by('title')
    if request.method == "POST":
        form = SubmitAnswer(request.POST, request.FILES)
        form.fields['problem'].queryset = problem_list
        if form.is_valid():
            post = form.save(commit=False)
            post.submit_time = timezone.now()
            post.user = request.user
            post.submit_file = None
            post.save()

            post.submit_file = request.FILES.get('submit_file')
            post.save()
            result = judge(file_name=post.submit_file.path,
                           problem=post.problem, language=post.language, submit=post)
            post.result = result
            post.save()
            update_statistics(post)
            return redirect('public_submit')
    else:
        form = SubmitAnswer()
        form.fields['problem'].queryset = problem_list
    all_submits = Submit.objects.filter(
        user=request.user).order_by('submit_time').reverse()
    for i in all_submits:
        i.source_code = read_source_code(i.submit_file)
        i.language_mode = i.language.editor_mode
    return render(request, 'public_submit.html', {'form': form, 'all_submits': all_submits})


@login_required
@public_auth_and_problem_exist
def submit_specific_problem(request, problem_id):
    problem = Problem.objects.get(pk=problem_id)
    initial_info = {'specific_problem': problem.title}
    if request.method == "POST":
        form = SubmitSpecificProblem(
            request.POST, request.FILES, initial=initial_info)
        if form.is_valid():
            post = form.save(commit=False)
            post.submit_time = timezone.now()
            post.user = request.user
            post.problem = problem
            post.submit_file = None
            post.save()
            post.submit_file = request.FILES.get('submit_file')
            post.save()
            result = judge(file_name=post.submit_file.path,
                           problem=post.problem, language=post.language, submit=post)
            post.result = result
            post.save()
            update_statistics(post)
            return redirect('submit_specific_problem', problem_id)
    else:
        form = SubmitSpecificProblem(initial=initial_info)
    all_submits = Submit.objects.filter(
        user=request.user, problem=problem, problem__is_public=True).order_by('submit_time').reverse()
    for i in all_submits:
        i.source_code = read_source_code(i.submit_file)
        i.language_mode = i.language.editor_mode
    return render(request, 'public_specific_problem_submit.html', {'form': form, 'all_submits': all_submits, 'problem_id': problem_id})


# @login_required
# @public_auth
# def ajax_submit_process(request):
#     file = request.GET.get('file')
#     problem_id = request.GET.get('problem')
#     lang_id = request.GET.get('language')
#     file_extension = None
#     file_name = file
#     problem_list = Problem.objects.filter(is_public=True).order_by('title')
#     try:
#         index = file_name[::-1].index('.')
#         try:
#             slash_index = file_name[::-1].index('/')
#             if index < slash_index:
#                 file_extension = file_name[::-1][:index][::-1]
#         except ValueError:
#             file_extension = file_name[::-1][:index][::-1]
#     except ValueError:
#         pass
#     total_lang = Language.objects.all()
#     best_lang = None
#     best_language_mode = None
#     if file_extension:
#         file_extension = file_extension.lower()
#         for i in total_lang:
#             if file_extension == i.extension.lower():
#                 best_lang = i.id
#                 best_language_mode = i.editor_mode
#                 break
#     if not best_lang and lang_id:
#         best_lang = int(lang_id)
#     best_problem = None
#     if not problem_id:
#         file_name = file
#         try:
#             index = file_name[::-1].index('\\')
#             file_name = file_name[::-1][:index][::-1]
#         except ValueError:
#             pass
#         for i in problem_list:
#             if i.title.lower() in file_name.lower():
#                 best_problem = i.id
#                 break
#     response_data = {'best_lang': best_lang, 'best_problem': best_problem,
#                      'best_language_mode': best_language_mode}
#     return JsonResponse(response_data, content_type="application/json")


def create_statistics(problem):
    try:
        problem = Statistics(problem=problem)
        problem.save()
    except IntegrityError:
        pass


def university_ranklists():
    statistics = Statistics.objects.filter(is_active=True)
    active_problem = {stat.problem: stat for stat in statistics}
    user_list = User.objects.filter(role__short_name="public")
    university_list = set([user.campus for user in user_list])
    university_user_list_dict = {campus: [] for campus in university_list}
    university_dict = {campus.id: campus for campus in university_list}
    for user in user_list:
        university_user_list_dict[user.campus].append(user)

    rating_list = list()
    for campus in university_user_list_dict:
        user_list = university_user_list_dict[campus]
        univ_rate = 0.0
        for user in user_list:
            problem = set()
            submit_list = Submit.objects.filter(user=user, result="Correct")
            for sub in submit_list:
                problem.add(sub.problem)
            user_rate = 0.0
            for pro in problem:
                if not pro in active_problem:
                    continue
                user_rate += difficulty(active_problem[pro])
            univ_rate += user_rate
        rating_list.append([round(univ_rate, 1), campus.id, len(user_list)])

    rating_list.sort(reverse=True)

    if rating_list:
        rating_list[0].append(1)
    for i in range(1, len(rating_list)):
        if rating_list[i][0] == rating_list[i-1][0]:
            rating_list[i].append('')
        else:
            rating_list[i].append(i+1)

    university_ranklists = list()
    for i in rating_list:
        univ_rank = {'rank': i[-1], 'university': university_dict[i[1]],
                     'user_count': i[2],  'point': i[0]}
        university_ranklists.append(univ_rank)
    return university_ranklists


def country_ranklists():
    statistics = Statistics.objects.filter(is_active=True)
    active_problem = {stat.problem: stat for stat in statistics}
    user_list = User.objects.filter(role__short_name="public")
    country_list = set([user.campus.country for user in user_list])
    country_user_list_dict = {country: [] for country in country_list}
    for user in user_list:
        country_user_list_dict[user.campus.country].append(user)

    rating_list = list()
    for country in country_user_list_dict:
        user_list = country_user_list_dict[country]
        country_rate = 0.0
        university_set = set()
        for user in user_list:
            university_set.add(user.campus)
            problem = set()
            submit_list = Submit.objects.filter(user=user, result="Correct")
            for sub in submit_list:
                problem.add(sub.problem)

            user_rate = 0.0
            for pro in problem:
                if not pro in active_problem:
                    continue
                user_rate += difficulty(active_problem[pro])
            country_rate += user_rate
        rating_list.append([round(country_rate, 1), country,
                            len(user_list), len(university_set)])

    rating_list.sort(reverse=True)

    if rating_list:
        rating_list[0].append(1)
    for i in range(1, len(rating_list)):
        if rating_list[i][0] == rating_list[i-1][0]:
            rating_list[i].append('')
        else:
            rating_list[i].append(i+1)

    country_ranklists = list()
    for i in rating_list:
        country_rank = {'rank': i[-1], 'country': i[1],
                        'user_count': i[2], 'university_count': i[3], 'point': i[0]}
        country_ranklists.append(country_rank)
    return country_ranklists


def user_ranklists():
    statistics = Statistics.objects.filter(is_active=True)
    active_problem = {i.problem: i for i in statistics}
    user_list = User.objects.filter(role__short_name="public")
    user_dict = {i.id: i for i in user_list}
    rating_list = list()
    for user in user_list:
        problem = set()
        submit_list = Submit.objects.filter(user=user, result="Correct")
        for sub in submit_list:
            problem.add(sub.problem)
        rate = 0.0
        for pro in problem:
            if not pro in active_problem:
                continue
            rate += difficulty(active_problem[pro])
        rating_list.append([round(rate, 1), user.id])

    rating_list.sort(reverse=True)

    if rating_list:
        rating_list[0].append(1)
    for i in range(1, len(rating_list)):
        if rating_list[i][0] == rating_list[i-1][0]:
            rating_list[i].append('')
        else:
            rating_list[i].append(i+1)

    user_ranklists = list()
    for i in rating_list:
        user_rank = {'rank': i[-1], 'user': user_dict[i[1]], 'point': i[0]}
        user_ranklists.append(user_rank)
    return user_ranklists


@login_required
@public_auth
def ranklists(request):
    user_rank = user_ranklists()
    university_rank = university_ranklists()
    country_rank = country_ranklists()

    return render(request, 'ranklists.html',
                  {
                      'user_ranklists': user_rank,
                      'university_ranklists': university_rank,
                      'country_ranklists': country_rank
                  }
                  )



@login_required
@admin_or_jury_auth
def public_user_submission(request):
    
    submission_list = Submit.objects.filter(user__role__short_name='public').order_by('submit_time').reverse()
    all_problems = set()
    for submit in submission_list:
        pro = (submit.problem.id, submit.problem.title)
        all_problems.add(pro)
    base_page = check_base_site(request)
    context = {'submission_list': submission_list, 'all_problems': all_problems, 'base_page': base_page, 'submit': 'hover'}
    return render(request, 'public_view_submission.html', context)


@login_required
@admin_or_jury_auth
def public_view_submission_filter(request):
    problem_id = int(request.GET.get('problem_id'))
    try:
        problem_title = Problem.objects.get(pk=problem_id).title
    except Problem.DoesNotExist:
        problem_title = None
    if problem_id == 0:
        all_submissions = Submit.objects.filter(user__role__short_name='public').order_by('submit_time').reverse()
        problem_title = "All problems"
    else:
        all_submissions = Submit.objects.filter(
            user__role__short_name='public', problem_id=problem_id).order_by('submit_time').reverse()
    return render(request, 'public_view_submission_filter.html', {'submission_list': all_submissions, 'problem_title': problem_title, 'submit': 'hover'})


@login_required
@admin_jury_auth_and_submit_exist
def public_submission_detail(request, submit_id):
    submit = Submit.objects.get(pk=submit_id)

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
               'submit_detail': submit_detail, 'base_page': base_page}
    return render(request, 'public_submission_detail.html', context)



@login_required
@admin_auth
def public_rejudge_submission_list(request):
    submission_list = Submit.objects.filter(user__role__short_name='public').order_by('submit_time').reverse()
    all_problems = set()

    for submit in submission_list:
        pro = (submit.problem.id, submit.problem.title)
        all_problems.add(pro)
    context = {'submission_list': submission_list, 'all_problems': all_problems,  'rejudge': 'hover'}
    return render(request, 'public_rejudge_submission_list.html', context)


@login_required
@admin_auth
def public_rejudge_submission_filter(request):
    problem_id = int(request.GET.get('problem_id'))

    try:
        problem_title = Problem.objects.get(pk=problem_id).title
    except Problem.DoesNotExist:
        problem_title = None
    if problem_id == 0:
        all_submissions = Submit.objects.filter(user__role__short_name='public').order_by('submit_time').reverse()
        problem_title = "All problems"
    else:
        all_submissions = Submit.objects.filter(
            user__role__short_name='public', problem_id=problem_id).order_by('submit_time').reverse()
    
    return render(request, 'public_rejudge_filter.html', {'submission_list': all_submissions, 'problem_title': problem_title, 'rejudge': 'hover'})

def update_rejudge_statistics(submit, previous_result):
    new_result = submit.result
    if new_result == "Correct": new_result = 1
    else: new_result = 0
    if previous_result == "Correct": previous_result = 1
    else:previous_result = 0
    
    if new_result == previous_result:
        return
    try:
        statistics = Statistics.objects.get(problem=submit.problem)
    except Statistics.DoesNotExist:
        return
    if previous_result == 1:
        statistics.accurate_submissions -= 1
    elif new_result == 1:
        statistics.accurate_submissions += 1
    if previous_result == 1:
        pre = Submit.objects.filter(user=submit.user, problem=submit.problem).exclude(pk=submit.pk)
        if not pre.filter(result="Correct"):
            statistics.accurate_users -= 1
    if new_result == 1:
        pre = Submit.objects.filter(user=submit.user, problem=submit.problem).exclude(pk=submit.pk)
        if not pre.filter(result="Correct"):
            statistics.accurate_users += 1
    statistics.save()

@login_required
@admin_auth
def ajax_public_rejudge(request):
    total_submits = request.GET.getlist('total_submit[]')
    rejudge_submits = [int(i) for i in total_submits]
    result_dict = {}
    for submit_id in rejudge_submits:
        try:
            submit = Submit.objects.get(pk=submit_id)
            previous_result = submit.result
            try:
                result = judge(file_name=submit.submit_file.path, problem=submit.problem,
                        language=submit.language, submit=submit, rejudge=True)
                submit.result = result
                submit.save()
                update_rejudge_statistics(submit, previous_result)
            except ValueError:
                result = "file not found"
            
        except Submit.DoesNotExist:
            result = 'no submitted'
        result_dict[submit_id] = result
    response_data = {'result': result_dict}
    return JsonResponse(response_data, content_type="application/json")


@login_required
@admin_auth_and_submit_exist
def public_single_rejudge(request, submit_id):
    single_submit = Submit.objects.get(pk=submit_id)
    submit = [single_submit]

    return render(request, 'public_single_user_rejudge.html', {'submit': submit, 'rejudge': 'hover'})


@login_required
@admin_auth
def public_multi_rejudge(request, problem_id, user_id):
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

    return render(request, 'public_single_user_rejudge.html', {'submit': specific_submissions, 'contest_id': specific_submissions[0].contest.pk, 'rejudge': 'hover'})


