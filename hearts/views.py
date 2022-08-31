from uuid import uuid4

from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView

from hearts.forms import NewPlayerForm
from hearts.models import Game, Player


class HomeTemplateView(TemplateView):
    """
    Home page.

    Should direct user to server browser or create new game.
    """

    template_name = 'hearts/home.html'


class NewPlayerFormView(FormView):
    """
    Form for creating a new Player.

    A Player must be created before anything else can happen. A player is
    identified through a browser cookie that contains the player id.
    """

    template_name = 'hearts/new-player.html'
    form_class = NewPlayerForm
    success_url = reverse_lazy('home')

    def form_valid(self, form: NewPlayerForm) -> HttpResponseRedirect:
        player = self.create_player(form.name)
        # TODO: Set cookie with player id.
        return super().form_valid(form)

    def create_player(self, name: str) -> Player:
        """
        Create a new Player.
        """


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
                {'id': str(uuid4())[:-8], 'seats': '1 / 4', 'deal': 3, 'time_elapsed': '<1 min'},
                {'id': str(uuid4())[:-8], 'seats': 'FULL', 'deal': 1, 'time_elapsed': '17 min'},
            ]
        })
        return context


class NewGameView(View):
    """
    View to handle creation of games.
    """

    def get(self, request) -> HttpResponseRedirect:
        """
        Handle simple GET request which will create a game and redirect to it.
        """
        game = self.create_game()
        return HttpResponseRedirect(
            reverse('game', kwargs={'game_id': game.id})
        )

    def create_game(self) -> Game:
        """
        Create a new game and return it.

        This should use the "logged in" user as player 1.
        """


class GameTemplateView(TemplateView):
    """
    Main view for the actual game.
    """

    template_name = 'hearts/game.html'
