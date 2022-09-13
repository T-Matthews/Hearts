"""hearts URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from hearts import views

urlpatterns = [
    # Home.
    path('', views.HomeTemplateView.as_view(), name='home'),

    # Create a new player.
    path('new-player/', views.NewPlayerFormView.as_view(), name='new_player'),

    # Server Browser.
    path('game-browser/', views.GameBrowserTemplateView.as_view(), name='game_browser'),

    # Game.
    path('game/', views.NewGameView.as_view(), name='new_game'),
    path('game/<str:game_id>/', views.GameTemplateView.as_view(), name='game'),
    path('game/<str:game_id>/state/', views.GameStateView.as_view(), name='game_state'),
    path('game/<str:game_id>/state/stream/', views.stream_game_state, name='game_state_stream'),

    # Django Admin.
    path('admin/', admin.site.urls),
]
