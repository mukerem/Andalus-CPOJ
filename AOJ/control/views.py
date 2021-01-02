from django.shortcuts import render, render_to_response, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from authentication.decorators import admin_auth, admin_auth_and_language_exist
from django.contrib import messages
from control.forms import EditScoreValues, LanguageRegister, EditLanguage
from control.models import Setting
from competitive.models import Language
# Create your views here.

@login_required
@admin_auth
def score_values(request):
    score_values = Setting.objects.all().order_by('name')
    return render(request, 'score_values.html', {'score_values': score_values})

@login_required
@admin_auth
def edit_score_values(request, score_id):
    try:
        score = Setting.objects.get(pk=score_id)
    except Setting.DoesNotExist:
        return render('homepage')
    if request.method == "POST":
        form = EditScoreValues(request.POST, instance=score)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            messages.success(request, score.name+" was update successfully.")
            return redirect('score_values')
    else:
        form = EditScoreValues(instance=score)

    return render(request, 'edit_score_values.html', {'form': form})




@login_required
@admin_auth
def language_list(request):
    language_list = Language.objects.all().order_by('name')
    return render(request, 'language_list.html', {'language_list': language_list})


@login_required
@admin_auth_and_language_exist
def edit_language(request, language_id):
    language = Language.objects.get(pk=language_id)
    if request.method == "POST":
        form = EditLanguage(request.POST, instance=language)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            messages.success(request, "The language "+language.name+" was update successfully.")
            return redirect('edit_language', language.id)
    else:
        form = EditLanguage(instance=language)

    return render(request, 'edit_language.html', {'form': form, 'language_id': language.id})



@login_required
@admin_auth_and_language_exist
def delete_language(request, language_id):
    language = Language.objects.get(pk=language_id)
    return render(request, 'delete_language.html', {'this_language': language})


@login_required
@admin_auth_and_language_exist
def delete_language_done(request, language_id):
    language = Language.objects.get(pk=language_id)
    language.delete()
    messages.success(request, "language " + language.name  + " was deleted successfully.")
    return redirect('language_list')
 

@login_required
@admin_auth
def language_register(request): 
    if request.method =="POST":
        form = LanguageRegister(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()  
            messages.success(request, "language "+post.name +" was added successfully.")
            return redirect('language_list')
    else:
        form = LanguageRegister()
    return render(request, 'language_register.html', {'form': form})
