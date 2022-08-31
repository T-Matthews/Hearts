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

    # Create a new game.
    path('new-game/', views.NewGameFormView.as_view(), name='new_game'),

    # Server Browser.
    path('game-browser/', views.GameBrowserTemplateView.as_view(), name='server_browser'),

    # Game.
    path('game/<str:game_id>/', views.GameView.as_view(), name='game'),

    # Django Admin.
    path('admin/', admin.site.urls),
]
