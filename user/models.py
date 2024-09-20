from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet

# 암호화를 위한 대칭키 생성
key = Fernet.generate_key()
cipher_suite = Fernet(key)

class ApiKey(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    access_key = models.CharField(max_length=255)
    secret_key = models.CharField(max_length=255)

    # 액세스 키를 암호화하여 저장하는 메서드
    def set_access_key(self, raw_access_key):
        self.access_key = cipher_suite.encrypt(raw_access_key.encode()).decode()

    # 액세스 키를 복호화하여 가져오는 메서드
    def get_access_key(self):
        return cipher_suite.decrypt(self.access_key.encode()).decode()

    # 시크릿 키를 암호화하여 저장하는 메서드
    def set_secret_key(self, raw_secret_key):
        self.secret_key = cipher_suite.encrypt(raw_secret_key.encode()).decode()

    # 시크릿 키를 복호화하여 가져오는 메서드
    def get_secret_key(self):
        return cipher_suite.decrypt(self.secret_key.encode()).decode()
