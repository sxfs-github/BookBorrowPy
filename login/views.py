from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.hashers import check_password

from .forms import ChangePasswordForm


@require_http_methods(["GET", "POST"])
def do_login(request):
    if request.method == 'GET':
        return render(request, 'login.html')

    username = request.POST.get('username', '')
    password = request.POST.get('password', '')

    user = authenticate(request, username=username, password=password)
    if user is not None:
        if check_password('sxfs123456', user.password):
            return render(request, 'edit_password.html', {
                'username': username
            })
        login(request, user)
        return redirect(reverse('book_borrow:index'))
    else:
        return render(request, 'login.html', {
            'username': username,
            'login_error': "用户名或密码错误"
        })


@login_required(login_url='login:login')
@require_POST
def do_logout(request):
    logout(request)
    return redirect(reverse('book_borrow:index'))


@require_POST
def change_password(request):
    form = ChangePasswordForm(request.POST)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = User.objects.get(username=username)
        user.set_password(password)
        user.save()
        return redirect(reverse('login:login'))
    else:
        return render(request, 'edit_password.html', {
            'username': request.POST.get('username', ''),
            'form': form
        })
