from django.urls import path, re_path

from hearts import consumers

websocket_urlpatterns = [
    path('game/<str:game_id>/socket/', consumers.GameConsumer.as_asgi(), name='game_socket'),
]
