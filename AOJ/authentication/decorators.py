from django.core.exceptions import PermissionDenied
from authentication.models import User, Role, Campus
from problem.models import Problem, TestCase
from contest.models import Contest
from competitive.models import Submit, Language
from clarification.models import Clarification
from django.utils import timezone
from django.shortcuts import redirect


def admin_auth(function):
    def wrap(request, *args, **kwargs):
        # admin = Role.objects.get(short_name='admin')
        if request.user.role.short_name == 'admin':
            return function(request, *args, **kwargs)
        else:
            # raise PermissionDenied
            return redirect('homepage')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def admin_auth_and_problem_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            Problem.objects.get(pk=kwargs['problem_id'])
        except Problem.DoesNotExist:
            raise PermissionDenied
        if request.user.role.short_name == 'admin':
            return function(request, *args, **kwargs)
        else:
            # raise PermissionDenied
            return redirect('homepage')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def admin_auth_and_testcase_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            TestCase.objects.get(pk=kwargs['testcase_id'])
        except TestCase.DoesNotExist:
            raise PermissionDenied
        if request.user.role.short_name == 'admin':
            return function(request, *args, **kwargs)
        else:
            # raise PermissionDenied
            return redirect('homepage')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def admin_auth_and_contest_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            Contest.objects.get(pk=kwargs['contest_id'])
        except Contest.DoesNotExist:
            raise PermissionDenied
        if request.user.role.short_name == 'admin':
            return function(request, *args, **kwargs)
        else:
            # raise PermissionDenied
            return redirect('homepage')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def admin_auth_and_user_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            User.objects.get(pk=kwargs['user_id'])
        except User.DoesNotExist:
            raise PermissionDenied
        if request.user.role.short_name == 'admin':
            return function(request, *args, **kwargs)
        else:
            # raise PermissionDenied
            return redirect('homepage')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def admin_auth_and_campus_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            Campus.objects.get(pk=kwargs['campus_id'])
        except Campus.DoesNotExist:
            raise PermissionDenied
        if request.user.role.short_name == 'admin':
            return function(request, *args, **kwargs)
        else:
            # raise PermissionDenied
            return redirect('homepage')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def admin_auth_and_language_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            Language.objects.get(pk=kwargs['language_id'])
        except Language.DoesNotExist:
            raise PermissionDenied
        if request.user.role.short_name == 'admin':
            return function(request, *args, **kwargs)
        else:
            # raise PermissionDenied
            return redirect('homepage')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def admin_auth_and_submit_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            Submit.objects.get(pk=kwargs['submit_id'])
        except Submit.DoesNotExist:
            raise PermissionDenied
        if request.user.role.short_name == 'admin':
            return function(request, *args, **kwargs)
        else:
            # raise PermissionDenied
            return redirect('homepage')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap



def admin_auth_and_clarification_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            clarification = Clarification.objects.get(pk=kwargs['clarification_id'])
            if clarification.contest.active_time > timezone.now() or \
                clarification.contest.deactivate_time < timezone.now():
                raise PermissionDenied
        except Clarification.DoesNotExist:
            # raise PermissionDenied
            return redirect('homepage')
        if request.user.role.short_name == 'admin':
            return function(request, *args, **kwargs)
        else:
            # raise PermissionDenied
            return redirect('homepage')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


# jury user decorator

def jury_auth(function):
    def wrap(request, *args, **kwargs):
        if request.user.role.short_name == 'jury':
            return function(request, *args, **kwargs)
        else:
            # raise PermissionDenied
            return redirect('homepage')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def jury_auth_and_problem_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            Problem.objects.get(pk=kwargs['problem_id'])
        except Problem.DoesNotExist:
            # raise PermissionDenied
            return redirect('homepage')
        if request.user.role.short_name == 'jury':
            return function(request, *args, **kwargs)
        else:
            # raise PermissionDenied
            return redirect('homepage')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def jury_auth_and_testcase_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            TestCase.objects.get(pk=kwargs['testcase_id'])
        except TestCase.DoesNotExist:
            # raise PermissionDenied
            return redirect('homepage')
        if request.user.role.short_name == 'jury':
            return function(request, *args, **kwargs)
        else:
            # raise PermissionDenied
            return redirect('homepage')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def jury_auth_and_contest_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            Contest.objects.get(pk=kwargs['contest_id'])
        except Contest.DoesNotExist:
            # raise PermissionDenied
            return redirect('homepage')
        if request.user.role.short_name == 'jury':
            return function(request, *args, **kwargs)
        else:
            # raise PermissionDenied
            return redirect('homepage')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def jury_auth_and_user_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            User.objects.get(pk=kwargs['user_id'])
        except User.DoesNotExist:
            # raise PermissionDenied
            return redirect('homepage')
        if request.user.role.short_name == 'jury':
            return function(request, *args, **kwargs)
        else:
            # raise PermissionDenied
            return redirect('homepage')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def jury_auth_and_submit_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            Submit.objects.get(pk=kwargs['submit_id'])
        except Submit.DoesNotExist:
            # raise PermissionDenied
            return redirect('homepage')
        if request.user.role.short_name == 'jury':
            return function(request, *args, **kwargs)
        else:
            # raise PermissionDenied
            return redirect('homepage')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def admin_or_jury_auth(function):
    def wrap(request, *args, **kwargs):
        if request.user.role.short_name == 'admin' or request.user.role.short_name == 'jury':
            return function(request, *args, **kwargs)
        else:
            # raise PermissionDenied
            return redirect('homepage')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap



# contestant participant user decorator

def contestant_auth(function):
    def wrap(request, *args, **kwargs):
        cont = Role.objects.get(short_name='contestant')
        if cont == request.user.role:
            return function(request, *args, **kwargs)
        else:
            # raise PermissionDenied
            return redirect('homepage')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def admin_jury_auth_and_contest_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            Contest.objects.get(pk=kwargs['contest_id'])
        except Contest.DoesNotExist:
            # raise PermissionDenied
            return redirect('homepage')
        if request.user.role.short_name == 'admin' or request.user.role.short_name == 'jury':
            return function(request, *args, **kwargs)
        else:
            # raise PermissionDenied
            return redirect('homepage')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def admin_jury_auth_and_submit_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            Submit.objects.get(pk=kwargs['submit_id'])
        except Submit.DoesNotExist:
            # raise PermissionDenied
            return redirect('homepage')
        if request.user.role.short_name == 'admin' or request.user.role.short_name == 'jury':
            return function(request, *args, **kwargs)
        else:
            # raise PermissionDenied
            return redirect('homepage')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


# public participant user decorator

def public_auth(function):
    def wrap(request, *args, **kwargs):
        cont = Role.objects.get(short_name='public')
        if cont == request.user.role:
            return function(request, *args, **kwargs)
        else:
            # raise PermissionDenied
            return redirect('homepage')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap

def public_auth_and_problem_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            Problem.objects.get(pk=kwargs['problem_id'])
        except Problem.DoesNotExist:
            # raise PermissionDenied
            return redirect('homepage')
        if request.user.role.short_name == 'public':
            return function(request, *args, **kwargs)
        else:
            # raise PermissionDenied
            return redirect('homepage')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
