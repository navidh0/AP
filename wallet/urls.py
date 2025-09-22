from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [
    path('', views.WalletDetailView.as_view(), name='wallet_detail'),
    path('add-funds/', views.AddFundsAjaxView.as_view(), name='add_funds_ajax'),
    path('pay-appointment/', views.PayAppointmentAjaxView.as_view(), name='pay_appointment_ajax'),
]