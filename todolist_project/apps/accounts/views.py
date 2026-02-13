from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages

import logging
logger = logging.getLogger(__name__)


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if not username or not password:
            messages.error(request, 'Utilizador e password são obrigatórios.')
            return render(request, 'accounts/register.html')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Utilizador já existe.')
            return render(request, 'accounts/register.html')
        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return redirect('task_list')
    return render(request, 'accounts/register.html')


def login_view(request):
    ip = request.META.get("REMOTE_ADDR")

    if request.method == 'POST':
        ### registrar tentativa de login
        logger.warning("login_attempt ip=%s, msg=%s", ip, "tentativa de login")
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            ### registrar login bem-sucedido
            logger.info("login_success ip=%s msg=%s", ip, "login bem-sucedido")
            login(request, user)
            return redirect('task_list')
        ### registrar login falhado
        logger.error("login_fail ip=%s msg=%s", ip, "login falhado")
        messages.error(request, 'Credenciais inválidas.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')
