from django import forms
from .models import ApiKey
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class ApiKeyForm(forms.ModelForm):
    class Meta:
        model = ApiKey
        fields = ['access_key', 'secret_key']

    # API 키를 저장할 때 암호화된 값을 저장하도록 설정
    def save(self, user, commit=True):
        instance = super().save(commit=False)
        instance.user = user
        instance.set_access_key(self.cleaned_data['access_key'])
        instance.set_secret_key(self.cleaned_data['secret_key'])
        if commit:
            instance.save()
        return instance

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='이메일')
    first_name = forms.CharField(max_length=30, required=True, label='이름')
    last_name = forms.CharField(max_length=30, required=False, label='성')

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user
