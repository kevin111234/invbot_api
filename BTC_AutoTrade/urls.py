from django.urls import path
from . import views

urlpatterns = [
    path('call_openai/', views.call_openai, name='call_openai'),
]
