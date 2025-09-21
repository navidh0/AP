from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [
    path('', views.WalletDetailView.as_view(), name='wallet_detail'),
    path('add-funds/', views.add_funds_ajax, name='add_funds_ajax'),
    path('pay-appointment/', views.pay_appointment_ajax, name='pay_appointment_ajax'),
]