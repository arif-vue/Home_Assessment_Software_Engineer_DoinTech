from django.urls import path
from core import consumers

websocket_urlpatterns = [
    path('ws/orders', consumers.OrderConsumer.as_asgi()),
]
