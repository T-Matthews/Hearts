from typing import Any, Optional
from uuid import uuid4

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import FormView, TemplateView

from hearts.forms import NewGameForm


class HomeTemplateView(TemplateView):
    """
    Home page.

    Should direct user to server browser or create new game.
    """

    template_name = 'hearts/home.html'


class NewGameFormView(FormView):
    """
    Form for creating a new game.

    A game is created now by first creating the player then creating the game
    and linking the player + 3 bots. For now the creation is stubbed.
    """

    template_name = 'hearts/new-game.html'
    form_class = NewGameForm

    # This will be set in the `create_new_game` function when ready.
    game: Optional[Any]

    def get_success_url(self) -> str:
        """
        Build the URL to redirect to.

        This cannot be defined statically as we need to template the URL with
        the ID of the game we just created.
        """
        return reverse('game', kwargs={'game_id': self.game.id})

    def form_valid(self, form: NewGameForm) -> HttpResponseRedirect:
        player = self.get_or_create_player(form.name)
        self.create_new_game(player)
        return super().form_valid(form)

    def get_or_create_player(self, name: str) -> Any:
        """
        Get or create a Player who is starting this game.

        For now, it will always create a player with the given name. Once we
        can identify a player on the client side, we can pass the player id and
        fetch the Player from the database if given.
        """

    def create_new_game(self, player: Any) -> None:
        """
        Create a new game.

        Link the real player to the game then link 3 bots. The player will be
        redirected to this game.
        """
        # Set game on class instance for access in other methods.
        self.game = None


class GameBrowserTemplateView(TemplateView):
    """
    Render list of available games.
    """

    template_name = 'hearts/game-browser.html'

    def get_context_data(self, **kwargs) -> dict:
        """
        Query for all in progress games.

        This will return a list of Model instances once that is merged in. For
        now this is some test data to test the templates.
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'games': [
                {'id': uuid4(), 'deal': 3, 'players': 1, 'difficulty': 'hard'},
                {'id': uuid4(), 'deal': 1, 'players': 4, 'difficulty': 'easy'},
                {'id': uuid4(), 'deal': 9, 'players': 2, 'difficulty': 'hard'},
                {'id': uuid4(), 'deal': 4, 'players': 0, 'difficulty': 'medium'},
            ]
        })
        return context


class GameTemplateView(TemplateView):
    """
    Main view for the actual game.
    """

    template_name = 'hearts/game.html'
