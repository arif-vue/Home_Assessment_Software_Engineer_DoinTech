from django.urls import path
from core import views

urlpatterns = [
    path('health', views.health_check),
    path('accounts', views.link_broker_account),
]
