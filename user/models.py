from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
from django.utils.crypto import get_random_string

class User(AbstractUser): # 기본 유저 모델
    pass

class APIKey(models.Model): # Api 키 저장 모델
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    api_key_encrypted = models.TextField()

    def set_api_key(self, raw_key):
        cipher_suite = Fernet(settings.SECRET_KEY)  # 대칭키 암호화
        encrypted_key = cipher_suite.encrypt(raw_key.encode())
        self.api_key_encrypted = encrypted_key.decode()

    def get_api_key(self):
        cipher_suite = Fernet(settings.SECRET_KEY)
        decrypted_key = cipher_suite.decrypt(self.api_key_encrypted.encode())
        return decrypted_key.decode()