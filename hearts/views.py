import json
import random
import time
from datetime import datetime, timezone
from uuid import uuid4

from asgiref.sync import sync_to_async
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse, StreamingHttpResponse,
)
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, TemplateView

from hearts.constants import PLAYER_ID_COOKIE_KEY
from hearts.decorators import require_player
from hearts.forms import NewPlayerForm
from hearts.game.manager import GameManager
from hearts.models import Card, Deal, Game, Player


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
        response = super().form_valid(form)
        player = self.create_player(form.cleaned_data['name'])
        response.set_cookie(PLAYER_ID_COOKIE_KEY, player.id)
        return response

    @staticmethod
    def create_player(name: str) -> Player:
        """
        Create a new Player.
        """
        player = Player.objects.create(name=name)
        return player


@method_decorator(require_player, name='dispatch')
class HomeTemplateView(TemplateView):
    """
    Home page.

    Should direct user to server browser or create new game.
    """

    template_name = 'hearts/home.html'

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context.update({
            'player': self.request.player,
        })
        return context


@method_decorator(require_player, name='dispatch')
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

        games = Game.objects.select_related(
            'player_1',
            'player_2',
            'player_3',
            'player_4',
        ).filter(
            winning_player__isnull=True,
        ).order_by('-created_at')

        my_games_to_display = []
        other_games_to_display = []
        for game in games:
            minutes_elapsed = (datetime.now(timezone.utc) - game.created_at).seconds // 60
            if minutes_elapsed <= 1:
                time_elapsed = '<1 minute'
            elif (hours_elapsed := minutes_elapsed // 60) > 0:
                if hours_elapsed == 1:
                    time_elapsed = f'{hours_elapsed} hour'
                else:
                    time_elapsed = f'{hours_elapsed} hours'
            else:
                time_elapsed = f'{minutes_elapsed} minutes'

            game_info = {
                'id': str(game.id),
                'seats': f'{len([p for p in game.players if p.bot])} / 4',
                'deal': Deal.objects.filter(game=game).count(),
                'time_elapsed': time_elapsed,
            }
            if self.request.player in game.players:
                my_games_to_display.append(game_info)
            else:
                other_games_to_display.append(game_info)

        context.update({
            'my_games': my_games_to_display[:6],
            'other_games': other_games_to_display[:6],
        })
        return context


@method_decorator(require_player, name='dispatch')
class NewGameView(View):
    """
    View to handle creation of games.
    """

    def get(self, request: HttpRequest) -> HttpResponse:
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
        return GameManager.new_game(self.request.player)


@method_decorator(require_player, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class GameTemplateView(TemplateView):
    """
    Main view for the actual game.
    """

    template_name = 'hearts/game.html'

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Join a game in progress."""
        game = Game.objects.get(id=kwargs['game_id'])
        GameManager(game).join(request.player)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context.update({'game_id': kwargs['game_id']})
        return context

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        request_data = json.loads(request.body)

        game = Game.objects.get(id=kwargs['game_id'])
        game_manager = GameManager(game)

        action_type = request_data['action_type']
        match action_type:
            case 'deal-cards':
                game_manager.new_deal()
                game_manager.new_trick()
            case 'pass-cards':
                cards = list(Card.objects.filter(
                    id__in=request_data['card_ids'],
                    player=request.player,
                ))
                game_manager.set_cards_to_pass(cards)
            case 'play-card':
                card = Card.objects.get(
                    id=request_data['card_id'],
                    player=request.player,
                )
                game_manager.play_card(card)
            case 'leave-game':
                game_manager.leave(request.player)
                return HttpResponse(status=200)
            case _:
                return HttpResponse(status=400)

        game_manager.play()
        game_manager.send_game_state_to_client()
        return HttpResponse(status=204)


@method_decorator(require_player, name='dispatch')
class GameStateView(View):

    def get(self, request: HttpRequest, game_id: str, *args, **kwargs) -> HttpResponse:
        game = Game.objects.get(id=game_id)

        player = self.request.player
        is_observer = False
        if player.id not in [p.id for p in game.players]:
            player = game.player_1
            is_observer = True

        game_manager = GameManager(game)
        game_state = game_manager.get_game_state(player, is_observer)

        return JsonResponse(game_state)


@require_player
def stream_game_state(request, *args, **kwargs):
    game = Game.objects.get(id=kwargs['game_id'])

    def game_state_stream():
        while True:
            time.sleep(0.5)
            player = request.player
            is_observer = False
            if player.id not in [p.id for p in game.players]:
                player = game.player_1
                is_observer = True

            game_state = GameManager(game).get_game_state(player, is_observer)
            yield 'data: %s\n\n' % json.dumps(game_state)

    return StreamingHttpResponse(
        sync_to_async(game_state_stream)(),
        content_type='text/event-stream'
    )
