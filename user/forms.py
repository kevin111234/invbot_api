from django import forms
from .models import ApiKey

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
