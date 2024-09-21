from django.urls import path
from . import views

urlpatterns = [
    path('fetch_upbit_data/', views.fetch_upbit_data, name='fetch_upbit_data'),
    path('analyze_data/', views.analyze_data_and_trade, name='analyze_data'),
    path('auto_trade/', views.auto_trade, name='auto_trade'),
]
