from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('api-key/register/', views.api_key_register_view, name='api_key_register'),
    path('update_openai_key/', views.update_openai_key, name='update_openai_key'),
]
