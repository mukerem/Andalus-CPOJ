from django.shortcuts import render, render_to_response, redirect
from django.contrib.auth.decorators import login_required
from .models import Problem, TestCase
from problem.forms import AddProblem, EditProblem, AddTestcase, AddProblemZIP
from django.contrib import messages
from django.utils import timezone
from authentication.decorators import admin_auth, admin_auth_and_problem_exist, admin_auth_and_testcase_exist,\
    contestant_auth
from authentication.validators import validate_testcase_in_file_extension, validate_testcase_out_file_extension,\
    validate_problem_file_extension
from django.core.exceptions  import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
import  os, sys
from zipfile import ZipFile, BadZipFile
from io import BytesIO
from django.db import IntegrityError
from contest.models import Contest
from public.views import create_statistics

@login_required
@admin_auth
def problem_list(request):
    total_problems = Problem.objects.all().order_by('pk').reverse()
    return render(request, 'all_problems.html', {'problem': total_problems, 'pro': 'hover'})

def addProblem(request):
    if request.method =="POST":
        form = AddProblem(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.pdf = None
            post.save()
            post.pdf = request.FILES.get('pdf')
            post.save()

            if post.is_public:
                create_statistics(post) # create statistics for this problem

            messages.success(request, "problem "+post.title+" was added successfully.")
            return redirect('testcase', post.pk)
    else:
        form = AddProblem()
    form1 = AddProblemZIP()
    return render(request, 'add_problem.html', {'form': form, 'form1': form1, 'pro': 'hover'})


@login_required
@admin_auth
def addProblemZIP(request):
    if request.method =="POST":
        form1 = AddProblemZIP(request.POST, request.FILES)
        if form1.is_valid():
            handle_zip_file(request, request.FILES.get('file'))
            return redirect('problem_list')
        
    else:
        form1 = AddProblemZIP()
    form = AddProblem()
    return render(request, 'add_problem.html', {'form': form, 'form1': form1, 'pro': 'hover'})


@login_required
@admin_auth_and_problem_exist
def edit_problem(request, problem_id):
    problem = Problem.objects.get(pk=problem_id)
    problem_pdf_path = problem.pdf.path
    if request.method == "POST":
        form = EditProblem(request.POST, request.FILES, instance=problem)
        if form.is_valid():
            post = form.save(commit=False)
            if request.FILES.get('pdf'):
                os.system('rm '+problem_pdf_path) 
            post.save()
            if post.is_public:
                create_statistics(post) # create statistics for this problem

            messages.success(request, "The problem "+problem.title+" was update successfully.") 
            return redirect('testcase', problem_id)    
                
    else:
        form = EditProblem(instance=problem)
    return render(request, 'edit_problem.html', 
                 {'form': form,'problem_id': problem.id, 'pro': 'hover'})



@login_required
@admin_auth_and_problem_exist
def delete_problem(request, problem_id):
    problem = Problem.objects.get(pk=problem_id)

    return render(request, 'delete_problem.html', {'problem': problem, 'pro': 'hover'})


@login_required   
@admin_auth_and_problem_exist
def delete_problem_done(request, problem_id):
    problem = Problem.objects.get(pk=problem_id)
    test_case = TestCase.objects.filter(problem=problem)
    for i in test_case:
        os.system('rm '+i.input.path) 
        os.system('rm '+i.output.path) 
    os.system('rm -R '+problem.pdf.path) 

    problem_include_contest = Contest.objects.filter(problem=problem)
    for contest in problem_include_contest:
        contest.last_update = timezone.now()
        contest.save()
    problem.delete()

    messages.success(request, "The problem " + problem.title + " was deleted successfully.")
    return redirect('problem_list')



@login_required   
@admin_auth_and_problem_exist
def testcase(request, problem_id):
    problem = Problem.objects.get(pk=problem_id)
    test_case = TestCase.objects.filter(problem=problem).order_by('name')
    if request.method == "POST":
        error_list = []
        for i in test_case:
            in_put = request.FILES.get(i.input)
            out_put = request.FILES.get(i.output)
            if in_put:
                try:
                    validate_testcase_in_file_extension(in_put)
                    os.system('rm '+i.input.path)
                    i.input = in_put                  
                except ValidationError:
                    error_list.append((i.name+' input'))
               
            if out_put:
                try:
                    validate_testcase_out_file_extension(out_put)  
                    os.system('rm '+i.output.path)  
                    i.output = out_put                
                except ValidationError:
                    error_list.append((i.name+' output'))
            i.save()

        form = AddTestcase(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)

            name = 't'+str(len(test_case)+1)
            post.problem = problem
            post.name = name
            post.save()
            messages.success(request, "testcase "+post.name+" was added successfully.")
        
        if error_list:
            messages.warning(request, "Unsupported file extension in "+ ', '.join(error_list))
        url = request.META['HTTP_REFERER']
        return redirect('testcase', problem_id)
    else:
        form = AddTestcase()
    return render(request, 'testcase.html', {'form': form, 'title': problem.title, 'test_case': test_case, "problem_id": problem.id, 'pro': 'hover'})


@login_required
@admin_auth_and_testcase_exist
def delete_testcase(request, testcase_id):
    test_case = TestCase.objects.get(pk=testcase_id)
    return render(request, 'delete_testcase.html', {'testcase': test_case, 'pro': 'hover'})


@login_required   
@admin_auth_and_testcase_exist
def delete_testcase_done(request, testcase_id):
    test_case = TestCase.objects.get(pk=testcase_id)
    os.system('rm '+test_case.input.path)
    os.system('rm '+test_case.output.path)
    test_case.delete()
    messages.success(request, "Testcase " + test_case.name + " was deleted successfully.")
    return redirect('testcase', test_case.problem.pk)
    


def sample_test_case(request, zip, problem):
    testcase_name = 1
    for i in zip.namelist():
        if i[-2:] == 'in' and i[:-2] + 'ans' in zip.namelist():
            in_filename = i
            in_data = zip.read(in_filename)
            out_filename = i[:-2] + 'ans'
            out_data = zip.read(out_filename)
        elif i[-2:] == 'in' and i[:-2] + 'out' in zip.namelist():
            in_filename = i
            in_data = zip.read(in_filename)
            out_filename = i[:-2] + 'out'
            out_data = zip.read(out_filename)
        else:
            continue
    
        input_file = InMemoryUploadedFile(BytesIO(in_data), 'file', in_filename, 'file/text', sys.getsizeof(in_data), None)
        output_file = InMemoryUploadedFile(BytesIO(out_data), 'file', out_filename, 'file/text', sys.getsizeof(out_data), None)
        
        test_case = TestCase(name='t' + str(testcase_name), input=input_file, output=output_file, problem=problem)
        test_case.save()
        testcase_name += 1


def handle_zip_file(request, problem_zip):
    all_file = problem_zip.file
    try:
        zip = ZipFile(all_file)
    except BadZipFile:
        messages.warning(request, 'The file format must be zip.')
        return redirect('add_problem_zip')   

    try:
        problem_pdf = zip.read('problem.pdf')
        _pro = InMemoryUploadedFile(BytesIO(problem_pdf), 'file', 'problem.pdf', 'pdf/pdf', sys.getsizeof(problem_pdf), None)
        try:
            info_byte = zip.read('info.ini')
            info = info_byte.decode('ASCII').split('\n')
            if len(info) == 1:
                info = info_byte.decode('ASCII').split(',')
            info_map = dict()
            for i in info:
                split = i.split('=')
                if i and not i == '':
                    pro_info = split[1].strip().replace("'", '').replace('"', '')
                    info_map[split[0].replace(' ','')]=pro_info
            try:
                title = info_map['title']
            except KeyError:
                messages.warning(request, 'There is no title attribute in info.ini file.')
                return redirect('add_problem_zip')
            try:
                ballon = info_map['ballon']
                ballon = '#' + ballon.replace('#', '')
            except KeyError:
                ballon = "#ffffff"
            try:
                short_name = info_map['short_name']
                if len(short_name)>10:
                    messages.warning(request, 'short name must be less than 10 charcters in attribute in info.ini file.')
                    return redirect('add_problem_zip')
            except KeyError:
                messages.warning(request, 'There is no short_name attribute in info.ini file.')
                return redirect('add_problem_zip')
            
            try:
                time_limit = info_map['time_limit']
                try:
                    time_limit = float(time_limit.replace(' ',''))
                except ValueError:
                    messages.warning(request, 'in info.ini file invalid value for time_limit attribute.')
                    return redirect('add_problem_zip')
            except KeyError:
                messages.warning(request, 'There is no time_limit attribute in info.ini file.')
                return redirect('add_problem_zip')
            try:
                point = info_map['point']
                try:
                    point = float(point.replace(' ',''))
                except ValueError:
                    messages.warning(request, 'in info.ini file invalid value for point attribute.')
                    return redirect('add_problem_zip')
            except KeyError:
                point = 1

            try:
                memory_limit = info_map['memory_limit']
                try:
                    memory_limit = float(memory_limit.replace(' ',''))
                except ValueError:
                    messages.warning(request, 'in info.ini file invalid value for memory_limit attribute.')
                    return redirect('add_problem_zip')
            except KeyError:
                memory_limit = None
            
            try:
                error = info_map['error']
                try:
                    error = float(error)
                except ValueError:
                    messages.warning(request, 'in info.ini file invalid value for error attribute.')
                    return redirect('add_problem_zip')
            except KeyError:
                error = 0.0
            try:
                problem = Problem(title=title, short_name=short_name, time_limit=time_limit, memory_limit=memory_limit, ballon=ballon, error=error)  
                problem.save()
                problem.pdf = _pro
                problem.save()

                if problem.is_public:
                    create_statistics(post.problem) # create statistics for this problem

                messages.success(request, "problem "+problem.title+" was added successfully.")
                sample_test_case(request, zip, problem)   
            except IntegrityError:
                messages.warning(request, 'The title already exists.')
                return redirect('add_problem_zip')
                 
        except KeyError:
            messages.warning(request, 'The info file name must be info.ini')
            return redirect('add_problem_zip')
    except KeyError:
        messages.warning(request, 'The problem name must be problem.pdf')
        return redirect('add_problem_zip')


# @login_required
# @contestant_auth
# def contestant_problem_view(request):
#     now = timezone.now()
#     all_contests = Contest.objects.filter(user=request.user, active_time__lte=now, deactivate_time__gt=now, enable=True)
#     if all_contests:
#         problem = all_contests[0].problem
#     return render(request, 'all_problems.html', {'problem': problem})
