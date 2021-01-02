from django.shortcuts import render, render_to_response, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from authentication.decorators import admin_auth, admin_auth_and_user_exist, admin_auth_and_campus_exist, jury_auth, contestant_auth
from authentication.models import User, Role, Campus
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.db import IntegrityError
from authentication.validators import email_validate
from contest.models import Contest
from contest.views import create_contest_session_admin, create_contest_session_contestant, refresh_contest_session_public,\
    refresh_contest_session_admin, refresh_contest_session_contestant
import csv
from django.views.generic import CreateView
from authentication.forms import PublicUserRegistrationForm, EditMyProfile, EditUserProfile, AddUser,\
    CSVUserUpload, ChangePassword, EditCampus, CampusRegister
from django.contrib.auth.forms import AuthenticationForm


# Create your views here.
def index(request):
    form = AuthenticationForm()
    if request.user.is_authenticated:
        return redirect('homepage')
    else:
        return render(request, 'registration/login.html', {'form': form})


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


@login_required
def homepage(request):
    if request.user.role.short_name == 'super':
        return redirect('/admin/')
    elif request.user.role.short_name == 'admin':
        create_contest_session_admin(request)
        return render(request, 'admin_index.html', {'myicpc': 'hover'})
    elif request.user.role.short_name == 'jury':
        create_contest_session_admin(request)
        return render(request, 'jury_index.html')
    elif request.user.role.short_name == 'contestant':
        create_contest_session_contestant(request)
        return redirect('submit')
    elif request.user.role.short_name == 'public':
        return render(request, 'public_index.html')

# class Register(CreateView):
#     model = User
#     fields = ["username", "name", "email",  "password"]
#     template_name = "register.html"
#     success_url = "/home/"

#     def form_valid(self, form):
#         form.instance.role.short_name = "public"
#         self.object = form.save()
#         return super().form_valid(form)


def register(request):
    if request.method == "POST":
        form = PublicUserRegistrationForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            try:
                role = Role.objects.get(short_name='public')
                post.role = role
                post.save()
                messages.success(request, "user "+post.name +
                                 " was register successfully.")
            except Role.DoesNotExist:
                pass
            return redirect('/home/')
    else:
        form = PublicUserRegistrationForm()
    return render(request, 'register.html', {'form': form})


@login_required
def profile(request):
    # user_role = request.user.role
    # user_register_date = request.user.register_date
    # user_score = request.user.rating
    # username = request.user.username
    # user_campus = request.user.campus.name
    # initial_info = {'_campus': user_campus, '_username': username, '_register_date': user_register_date, '_rating': user_score}
    if request.method == "POST":
        form = EditMyProfile(request.POST, instance=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            messages.success(request, "successfully update.")
            return redirect('profile')
    else:
        form = EditMyProfile(instance=request.user)

    base = check_base_site(request)
    return render(request, 'profile.html', {'form': form, 'base_site': base})


@login_required
def change_password(request):
    if request.method == "POST":

        form = ChangePassword(request.POST, password=request.user.password)
        if form.is_valid():
            new_password = request.POST.get('new_password')
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, "The password was changed successfully.")
    else:
        form = ChangePassword(password=request.user.password)

    base = check_base_site(request)
    return render(request, 'change_password.html', {'form': form,  'base_site': base})


@login_required
@admin_auth
def user_list(request):

    contestant_user = User.objects.filter(
        role__short_name="contestant").order_by('username')
    admin_user = User.objects.filter(
        role__short_name="admin").order_by('username')
    jury_user = User.objects.filter(
        role__short_name="jury").order_by('username')
    public_user = User.objects.filter(
        role__short_name="public").order_by('username')

    context = {
        'contestant_user': contestant_user,
        'admin_user': admin_user,
        'jury_user': jury_user,
        'public_user': public_user,
        'user': 'hover'
    }
    return render(request, 'user_list.html', context)


@login_required
@admin_auth_and_user_exist
def delete_user(request, user_id):
    user = User.objects.get(pk=user_id)
    return render(request, 'delete_user.html', {'this_user': user, 'user': 'hover'})


@login_required
@admin_auth_and_user_exist
def delete_user_done(request, user_id):
    user = User.objects.get(pk=user_id)
    # user_participated_contest = Contest.objects.filter(user=user)
    # for contest in user_participated_contest:
    #     contest.last_update = timezone.now()
    #     contest.save()
    user.delete()
    messages.success(request, "user " + user.name +
                     " was deleted successfully.")
    return redirect('user')


@login_required
@admin_auth_and_user_exist
def edit_user(request, user_id):
    user = User.objects.get(pk=user_id)
    if request.method == "POST":
        form = EditUserProfile(request.POST, instance=user)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            messages.success(request, "The user " +
                             user.username+" was update successfully.")
            return redirect('user')
    else:
        form = EditUserProfile(instance=user)

    return render(request, 'edit_user.html', {'form': form, 'user_id': user.id, 'user': 'hover'})


@login_required
@admin_auth
def user_register(request):
    role_list = Role.objects.all().exclude(short_name='super')
    if request.method == "POST":
        form = AddUser(request.POST)
        form.fields['role'].queryset = role_list
        if form.is_valid():
            chars = 'abcdefghijklmnopqrstuvwxyz0123456789@#$%&*'
            secret_key = get_random_string(8, chars)
            post = form.save(commit=False)
            post.set_password(secret_key)
            post.save()
            messages.success(request, "user "+post.name +
                             " was added successfully.")
            return redirect('user_register')
    else:
        form = AddUser()
        form.fields['role'].queryset = role_list
    form1 = CSVUserUpload()
    return render(request, 'user_register.html', {'form': form, 'form1': form1, 'user': 'hover'})


def validate_data(request, username, name, email, line_number):
    if not username:
        messages.error(request, "invalid username in line " + str(line_number))
        return 0
    else:
        try:
            User.objects.get(username=username)
            messages.error(request, "username " +
                           username + " was already exists.")
            return 0
        except User.DoesNotExist:
            pass

    if not name:
        messages.error(request, "invalid name for user " + username)
        return 0

    if email and not email_validate(email):
        messages.error(request, "invalid email for user " + username)
        return 0

    return 1


def register_csv(request, csv_file):
    if not (csv_file.content_type == 'text/csv' or csv_file.content_type == 'application/vnd.ms-excel'):
        messages.error(request, "The file is not csv format.")
        return redirect('user_register_csv')
    else:
        decoded_file = csv_file.read().decode('utf-7').splitlines()
        reader = csv.DictReader(decoded_file)
        line_number = 0
        for row in reader:
            # basic info
            try:
                username = row['username'].strip()
                name = row['name'].strip()
                email = row['email'].strip()
                role = row['role'].strip()
                campus_short_name = row['campus']
            except KeyError:
                messages.error(request, "invalid column header in csv file.Column headers must be contain username,"
                               " name, email, role and campus.")
                return redirect('user_register_csv')

            # validate data
            val = validate_data(request, username, name, email, line_number)

            if val == 0:
                continue

            # role info
            try:
                role = Role.objects.get(short_name=role)
                if role.short_name == 'super':
                    messages.error(
                        request, "the role of {} is super admin, it is not valid".format(username))
                    continue
            except Role.DoesNotExist:
                messages.error(request, "invalid role for user " + username)
                continue

            # campus info
            if not campus_short_name.replace(' ', '') == '':
                try:
                    campus = Campus.objects.get(short_name=campus_short_name)
                except Campus.DoesNotExist:
                    messages.error(
                        request, "invalid campus for user " + username)
                    continue
            else:
                campus = None
            try:
                chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
                if 'password' in row:
                    secret_key = row['password']
                else:
                    secret_key = get_random_string(8, chars)
                obj, created = User.objects.get_or_create(
                    username=username,
                    name=name,
                    email=email,
                    campus=campus,
                    role=role,
                )
                obj.set_password(secret_key)
                obj.save()

            except IntegrityError:
                messages.error(
                    request, "invalid information for user " + username)
            line_number += 1
    if not line_number:
        messages.error(request, " no user register.")
    else:
        messages.success(request, str(line_number) +
                         " user register successfully.")
    return redirect('user_register_csv')


@login_required
@admin_auth
def user_register_csv(request):
    if request.method == "POST":
        form1 = CSVUserUpload(request.POST, request.FILES)
        if form1.is_valid():
            file = request.FILES.get('file')
            register_csv(request, file)
            return redirect('user_register')
    else:
        form1 = CSVUserUpload()
    form = AddUser()
    return render(request, 'user_register.html', {'form': form, 'form1': form1, 'user': 'hover'})


def generate_users_password_csv(request, total_users):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="User Password Generate.csv"'
    writer = csv.writer(response)
    writer.writerow(['#', 'Username', 'Name', 'Role', 'Password'])
    for user in total_users:
        writer.writerow(user)
    return response


@login_required
@admin_auth
def generate_user_password(request, role_type):
    role = Role.objects.get(short_name=role_type)
    return render(request, 'generate_password.html', {'role': role})


@login_required
@admin_auth
def generate_password_done(request, role_id):
    role = Role.objects.get(pk=role_id)
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    total_users = []
    count = 1
    all_users = User.objects.filter(role=role)
    for user in all_users:
        secret_key = get_random_string(6, chars)
        user.set_password(secret_key)
        user.save()
        total_users.append((count, user.username, user.name,
                            user.role.role, secret_key))
        count += 1
    excel = generate_users_password_csv(request, total_users)
    return excel

    return redirect('user_list')


@login_required
@admin_auth
def setting(request):
    return render(request, 'setting.html')


@login_required
@admin_auth
def campus_list(request):
    campus_list = Campus.objects.all().order_by('name')
    return render(request, 'campus_list.html', {'campus_list': campus_list})


@login_required
@admin_auth_and_campus_exist
def edit_campus(request, campus_id):
    campus = Campus.objects.get(pk=campus_id)
    if request.method == "POST":
        form = EditCampus(request.POST, request.FILES, instance=campus)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            messages.success(request, "The campus " +
                             campus.name+" was update successfully.")
            return redirect('edit_campus', campus.id)
    else:
        form = EditCampus(instance=campus)

    return render(request, 'edit_campus.html', {'form': form, 'campus_id': campus.id})


@login_required
@admin_auth_and_campus_exist
def delete_campus(request, campus_id):
    campus = Campus.objects.get(pk=campus_id)
    return render(request, 'delete_campus.html', {'this_campus': campus})


@login_required
@admin_auth_and_campus_exist
def delete_campus_done(request, campus_id):
    campus = Campus.objects.get(pk=campus_id)
    campus.delete()
    messages.success(request, "campus " + campus.name +
                     " was deleted successfully.")
    return redirect('campus_list')


@login_required
@admin_auth
def campus_register(request):
    if request.method == "POST":
        form = CampusRegister(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            messages.success(request, "campus "+post.name +
                             " was added successfully.")
            return redirect('campus_list')
    else:
        form = CampusRegister()
    return render(request, 'campus_register.html', {'form': form})
