from django.db import models
from django.conf import settings

class ApiKey(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    access_key = models.CharField(max_length=255)
    secret_key = models.CharField(max_length=255)

    # 액세스 키를 암호화하여 저장하는 메서드
    def set_access_key(self, raw_access_key):
        self.access_key = settings.CIPHER_SUITE.encrypt(raw_access_key.encode()).decode()

    # 액세스 키를 복호화하여 가져오는 메서드
    def get_access_key(self):
        return settings.CIPHER_SUITE.decrypt(self.access_key.encode()).decode()

    # 시크릿 키를 암호화하여 저장하는 메서드
    def set_secret_key(self, raw_secret_key):
        self.secret_key = settings.CIPHER_SUITE.encrypt(raw_secret_key.encode()).decode()

    # 시크릿 키를 복호화하여 가져오는 메서드
    def get_secret_key(self):
        return settings.CIPHER_SUITE.decrypt(self.secret_key.encode()).decode()
