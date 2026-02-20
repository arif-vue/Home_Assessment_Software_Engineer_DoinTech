from django.urls import path
from core import views

urlpatterns = [
    path('health', views.health_check),
    path('auth/token', views.obtain_token),
    path('accounts', views.link_broker_account),
    path('webhook/receive-signal', views.receive_signal),
    path('orders', views.list_orders),
    path('orders/<str:order_id>', views.order_detail),
    path('analytics', views.analytics),
]
