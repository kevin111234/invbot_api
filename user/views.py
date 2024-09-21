from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import ApiKeyForm, CustomUserCreationForm
from .forms import OpenAIKeyForm

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('home')  # 로그아웃 후 홈으로 리디렉션
    return render(request, 'logout.html')

@login_required
def api_key_register_view(request):
    if request.method == 'POST':
        form = ApiKeyForm(request.POST)
        if form.is_valid():
            form.save(user=request.user)
            return redirect('home')  # 등록 후 홈으로 이동
    else:
        form = ApiKeyForm()
    return render(request, 'api_key_register.html', {'form': form})

@login_required
def update_openai_key(request):
    user_profile = request.user.userprofile
    if request.method == 'POST':
        form = OpenAIKeyForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('home')  # 프로필 페이지로 리다이렉트
    else:
        form = OpenAIKeyForm(instance=user_profile)
    return render(request, 'update_openai_key.html', {'form': form})
