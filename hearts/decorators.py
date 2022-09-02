from typing import Callable

from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse

from hearts.constants import PLAYER_ID_COOKIE_KEY
from hearts.models import Player


def require_player(func: Callable) -> Callable:
    """
    Decorator to require Player identification on views.

    This should only be used on the `dispatch` method of class views.
    """
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Wrap the `dispatch` method and add extra logic.

        - Get played_id from browser cookie
        - Use player_id to get Player from database
        - Set `request.player` to the Player object found
        - Redirect to `new-player` page if can't identify player
        """
        player_id = request.COOKIES.get(PLAYER_ID_COOKIE_KEY)
        new_player_url = reverse('new_player')
        if not player_id:
            return HttpResponseRedirect(new_player_url)

        try:
            request.player = Player.objects.get(id=player_id)
        except Player.DoesNotExist:
            return HttpResponseRedirect(new_player_url)

        return func(request, *args, **kwargs)
    return wrapper
