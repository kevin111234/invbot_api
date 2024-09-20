from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
from django.utils.crypto import get_random_string

class User(AbstractUser): # 기본 유저 모델
    pass
